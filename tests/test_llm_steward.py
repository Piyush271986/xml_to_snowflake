"""Tests for the Claude-backed Step 1 Data Steward Agent (no network: Anthropic transport is faked)."""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

from src.agents.a0_intake import run_a0_intake
from src.agents.c0_bootstrap import run_data_steward_agent
from src.llm.anthropic_client import ClaudeClient, LLMConfig
from src.models import DataModelSpec, LayerSchemaYaml
from src.sample_generator import generate_samples

TEST_CFG = LLMConfig(
    enabled=True,
    provider="anthropic",
    model="claude-haiku-5-5",
    max_tokens=16000,
    temperature=0.0,
    timeout_seconds=30,
    max_retries=0,
    send_sample_values=False,
    fail_if_unavailable=False,
    api_key_env="ANTHROPIC_API_KEY",
)


class _FakeMessages:
    def __init__(self, tool_input: dict[str, Any] | None, stop_reason: str = "tool_use", raise_exc: bool = False):
        self.tool_input = tool_input
        self.stop_reason = stop_reason
        self.raise_exc = raise_exc
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.raise_exc:
            raise RuntimeError("simulated API outage")
        block = SimpleNamespace(type="tool_use", name="submit_data_model", input=self.tool_input)
        return SimpleNamespace(stop_reason=self.stop_reason, content=[block])


class _FakeAnthropic:
    def __init__(self, messages: _FakeMessages):
        self.messages = messages


class TestClaudeDataStewardAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="xml_sf_llm_test_"))
        generate_samples(self.tmp_dir)
        self.registry_root = self.tmp_dir / "registry"
        self.manifest = run_a0_intake(
            dataset="orders",
            source_system="erp_orders",
            sample_dir=self.tmp_dir / "samples" / "orders",
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/orders/",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _load(self, name: str) -> dict[str, Any]:
        return yaml.safe_load((self.registry_root / "orders" / name).read_text(encoding="utf-8"))

    def test_claude_annotations_applied_and_unknown_columns_dropped(self) -> None:
        fake = _FakeMessages(
            {
                "summary": "Order header with line items.",
                "column_annotations": [
                    {"column": "order_id", "description": "Unique order identifier", "semantic_entity": "order_header",
                     "pii_category": "NONE", "suggested_name": None},
                    {"column": "customer_id", "description": "Customer account reference",
                     "semantic_entity": "customer", "pii_category": "NONE", "suggested_name": "customer_account_id"},
                    {"column": "hallucinated_col", "description": "x", "semantic_entity": "x", "pii_category": "NONE"},
                ],
                "gold_entities": [
                    {"name": "fact_order_line", "entity_type": "FACT", "grain": "one row per order line",
                     "primary_keys": ["order_id", "line_item_product_code"],
                     "columns": ["order_id", "line_item_product_code", "not_a_column"]},
                    {"name": "dim_ghost", "entity_type": "DIMENSION", "grain": "x", "primary_keys": [],
                     "columns": ["nope"]},
                ],
                "steward_review_notes": ["Confirm order_id is globally unique."],
            }
        )
        client = ClaudeClient(TEST_CFG, client=_FakeAnthropic(fake))
        run_data_steward_agent(self.manifest, self.registry_root, llm_client=client)

        # Request went to the configured Haiku model with forced tool use and no sample values
        call = fake.calls[0]
        self.assertEqual(call["model"], "claude-haiku-5-5")
        self.assertEqual(call["tool_choice"], {"type": "tool", "name": "submit_data_model"})
        self.assertNotIn('"samples"', call["messages"][0]["content"])

        dm = DataModelSpec.model_validate(self._load("data_model.yaml"))
        self.assertEqual(dm.modeling_engine, "anthropic_claude")
        self.assertEqual(dm.llm_model, "claude-haiku-5-5")
        assert dm.llm_proposal is not None
        self.assertEqual({a.column for a in dm.llm_proposal.column_annotations}, {"order_id", "customer_id"})
        self.assertEqual([e.name for e in dm.llm_proposal.gold_entities], ["fact_order_line"])
        self.assertEqual(dm.llm_proposal.gold_entities[0].columns, ["order_id", "line_item_product_code"])

        stg = LayerSchemaYaml.model_validate(self._load("staging_schema.yaml"))
        cols = {c.name: c for c in stg.tables[0].columns}
        self.assertEqual(cols["order_id"].description, "Unique order identifier")
        self.assertEqual(cols["customer_id"].suggested_name, "customer_account_id")
        # Suggestions never rename executable columns
        self.assertIn("customer_id", cols)
        self.assertFalse((self.registry_root / "orders" / "ddl.sql").exists())

        report = (self.registry_root / "orders" / "bootstrap_report.md").read_text(encoding="utf-8")
        self.assertIn("Anthropic Claude (`claude-haiku-5-5`)", report)
        self.assertIn("fact_order_line", report)

    def test_falls_back_to_rule_based_when_claude_fails(self) -> None:
        client = ClaudeClient(TEST_CFG, client=_FakeAnthropic(_FakeMessages(None, raise_exc=True)))
        mapping = run_data_steward_agent(self.manifest, self.registry_root, llm_client=client)
        self.assertGreater(len(mapping.fields), 0)
        dm = DataModelSpec.model_validate(self._load("data_model.yaml"))
        self.assertEqual(dm.modeling_engine, "rule_based")
        self.assertIn("simulated API outage", dm.llm_note or "")

    def test_truncated_response_falls_back(self) -> None:
        client = ClaudeClient(TEST_CFG, client=_FakeAnthropic(_FakeMessages({}, stop_reason="max_tokens")))
        run_data_steward_agent(self.manifest, self.registry_root, llm_client=client)
        dm = DataModelSpec.model_validate(self._load("data_model.yaml"))
        self.assertEqual(dm.modeling_engine, "rule_based")
        self.assertIn("max_tokens", dm.llm_note or "")

    def test_no_api_key_uses_rule_based(self) -> None:
        saved = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            run_data_steward_agent(self.manifest, self.registry_root)
        finally:
            if saved is not None:
                os.environ["ANTHROPIC_API_KEY"] = saved
        dm = DataModelSpec.model_validate(self._load("data_model.yaml"))
        self.assertEqual(dm.modeling_engine, "rule_based")


if __name__ == "__main__":
    unittest.main()

