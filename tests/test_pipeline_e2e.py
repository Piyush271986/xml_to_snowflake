"""End-to-end test suite for the XML-to-Snowflake agent-assisted pipeline."""
from __future__ import annotations

from contextlib import closing
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

import yaml

from src.agents.a3_quality_gates import evaluate_file_through_gates
from src.agents.a5_smoke_test import ingest_xml_files_into_warehouse
from src.models import ContractSpec, DatasetMapping, QualityRulesSpec
from src.orchestrator import (
    process_runtime_file_with_drift_control,
    run_full_onboarding_workflow,
)
from src.sample_generator import generate_samples


class TestXmlToSnowflakePipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="xml_sf_test_"))
        generate_samples(self.tmp_dir)
        self.sample_dir = self.tmp_dir / "samples" / "orders"
        self.drift_dir = self.tmp_dir / "samples" / "orders_drift"
        self.registry_root = self.tmp_dir / "registry"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_1_full_onboarding_and_c0_inference(self) -> None:
        """Verify Stages 1-10 onboarding, C0 type/array/confidence inference, and A5 smoke test."""
        result = run_full_onboarding_workflow(
            dataset="orders",
            source_system="erp_orders",
            sample_dir=self.sample_dir,
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/orders/",
            auto_approve_gates=True,
        )

        self.assertEqual(result["status"], "PUBLISHED")
        self.assertTrue(result["smoke_test"]["smoke_test_passed"])
        self.assertEqual(result["smoke_test"]["files_passed"], 10)
        self.assertEqual(result["smoke_test"]["quarantine_open_rows"], 0)
        self.assertEqual(result["smoke_test"]["curated_current_rows"], 15)

        # Inspect generated C4 Registry mapping.yaml
        ds_reg = self.registry_root / "orders"
        mapping = DatasetMapping.model_validate(
            yaml.safe_load((ds_reg / "mapping.yaml").read_text(encoding="utf-8"))
        )
        by_col = {f.column: f for f in mapping.fields}

        # Verify narrowest Snowflake type ladder
        self.assertEqual(by_col["order_id"].snowflake_type, "NUMBER(18,0)")
        self.assertTrue(by_col["order_id"].required)
        self.assertEqual(by_col["order_date"].snowflake_type, "DATE")
        self.assertEqual(by_col["order_timestamp"].snowflake_type, "TIMESTAMP_NTZ")
        self.assertEqual(by_col["is_expedited"].snowflake_type, "BOOLEAN")
        self.assertEqual(by_col["total_amount"].snowflake_type, "NUMBER(18,4)")

        # Verify low-confidence optional fields flagged for C3 review
        self.assertFalse(by_col["discount_amount"].required)
        self.assertEqual(by_col["discount_amount"].confidence, 0.5)
        self.assertFalse(by_col["shipping_notes"].required)
        self.assertEqual(by_col["shipping_notes"].confidence, 0.6)

        # Verify cardinality / array LATERAL FLATTEN detection
        self.assertTrue(by_col["line_item_product_code"].is_array)
        self.assertEqual(by_col["line_item_product_code"].flatten_path, "/Order/LineItems/LineItem")
        self.assertEqual(by_col["line_item_quantity"].snowflake_type, "NUMBER(18,0)")

        # Verify generated Snowflake DDL contains Snowpipe, Stream, LATERAL FLATTEN, and SCD2
        ddl_text = (ds_reg / "ddl.sql").read_text(encoding="utf-8")
        self.assertIn("CREATE PIPE IF NOT EXISTS pipe_orders", ddl_text)
        self.assertIn("LATERAL FLATTEN", ddl_text)
        self.assertIn("is_valid_start", ddl_text)
        self.assertIn("is_current", ddl_text)

    def test_2_additive_drift_auto_applied(self) -> None:
        """Verify C1/C2 auto-apply additive XML elements (PromoCode, LoyaltyTier) without human block."""
        run_full_onboarding_workflow(
            dataset="orders",
            source_system="erp_orders",
            sample_dir=self.sample_dir,
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/orders/",
            auto_approve_gates=True,
        )

        additive_file = self.drift_dir / "order_additive_drift.xml"
        res = process_runtime_file_with_drift_control(
            dataset="orders",
            xml_file=additive_file,
            registry_root=self.registry_root,
        )
        self.assertEqual(res["proposal_status"], "AUTO_APPLIED")
        self.assertEqual(res["proposed_version"], "0.2.0")
        self.assertEqual(res["ingest_metrics"]["files_passed"], 1)
        self.assertEqual(res["ingest_metrics"]["quarantine_open_rows"], 0)

        # Verify new columns exist in mapping.yaml and curated_orders
        ds_reg = self.registry_root / "orders"
        mapping = DatasetMapping.model_validate(
            yaml.safe_load((ds_reg / "mapping.yaml").read_text(encoding="utf-8"))
        )
        cols = {f.column for f in mapping.fields}
        self.assertIn("promo_code", cols)
        self.assertIn("loyalty_tier", cols)

    def test_3_breaking_drift_held_for_c3_and_quarantined_in_o3(self) -> None:
        """Verify breaking drift (missing required OrderDate & non-numeric OrderId) halts for C3 and routes to O3."""
        run_full_onboarding_workflow(
            dataset="orders",
            source_system="erp_orders",
            sample_dir=self.sample_dir,
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/orders/",
            auto_approve_gates=True,
        )

        breaking_file = self.drift_dir / "order_breaking_drift.xml"
        res = process_runtime_file_with_drift_control(
            dataset="orders",
            xml_file=breaking_file,
            registry_root=self.registry_root,
        )
        self.assertEqual(res["proposal_status"], "PENDING_C3_APPROVAL")
        self.assertEqual(res["proposed_version"], "1.0.0")
        self.assertEqual(res["ingest_metrics"]["files_quarantined"], 1)
        self.assertEqual(res["ingest_metrics"]["quarantine_open_rows"], 1)

        # Also test G1 malformed XML routing to O3 Quarantine
        malformed_file = self.drift_dir / "order_malformed.xml"
        ds_reg = self.registry_root / "orders"
        g1_metrics = ingest_xml_files_into_warehouse([malformed_file], ds_reg)
        self.assertEqual(g1_metrics["files_quarantined"], 1)
        self.assertEqual(g1_metrics["quarantine_open_rows"], 2)

        with closing(sqlite3.connect(ds_reg / "local_warehouse.db")) as conn:
            cur = conn.cursor()
            cur.execute("SELECT file_name, gate_id, failure_reason FROM quarantine_orders ORDER BY file_name")
            q_rows = cur.fetchall()
            self.assertEqual(len(q_rows), 2)
            self.assertEqual(q_rows[0][0], "order_breaking_drift.xml")
            self.assertEqual(q_rows[0][1], "G2")
            self.assertEqual(q_rows[1][0], "order_malformed.xml")
            self.assertEqual(q_rows[1][1], "G1")


if __name__ == "__main__":
    unittest.main()
