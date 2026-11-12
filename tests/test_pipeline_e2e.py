"""End-to-end test suite for the XML-to-Snowflake agent-assisted pipeline."""
from __future__ import annotations

from contextlib import closing
import os
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
    approve_c3_go_live,
    process_runtime_file_with_drift_control,
    run_full_onboarding_workflow,
)
from src.sample_generator import generate_samples
from src.snowflake_client import update_snowflake_config


class TestXmlToSnowflakePipeline(unittest.TestCase):
    def setUp(self) -> None:
        # Keep E2E tests deterministic and offline even if ANTHROPIC_API_KEY is set
        self._saved_llm_flag = os.environ.get("XML_PIPELINE_LLM_ENABLED")
        os.environ["XML_PIPELINE_LLM_ENABLED"] = "false"
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="xml_sf_test_"))
        generate_samples(self.tmp_dir)
        self.sample_dir = self.tmp_dir / "samples" / "orders"
        self.drift_dir = self.tmp_dir / "samples" / "orders_drift"
        self.registry_root = self.tmp_dir / "registry"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        if self._saved_llm_flag is None:
            os.environ.pop("XML_PIPELINE_LLM_ENABLED", None)
        else:
            os.environ["XML_PIPELINE_LLM_ENABLED"] = self._saved_llm_flag

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

        # Verify generated Snowflake DDL contains schema-qualified Snowpipe, Dynamic Tables, LATERAL FLATTEN, and SCD2
        ddl_text = (ds_reg / "ddl.sql").read_text(encoding="utf-8")
        self.assertIn("CREATE PIPE IF NOT EXISTS RAW.pipe_orders", ddl_text)
        self.assertIn("CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_orders", ddl_text)
        self.assertIn("CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_orders", ddl_text)
        self.assertIn("LATERAL FLATTEN", ddl_text)
        self.assertIn("valid_start_time", ddl_text)
        self.assertIn("is_current", ddl_text)

        # Verify 3-layer YAML schemas & pipeline deployment artifacts exist
        self.assertTrue((ds_reg / "raw_schema.yaml").exists())
        self.assertTrue((ds_reg / "staging_schema.yaml").exists())
        self.assertTrue((ds_reg / "gold_schema.yaml").exists())
        self.assertTrue((ds_reg / "data_model.yaml").exists())
        self.assertTrue((ds_reg / "pipeline_deployment_manifest.yaml").exists())
        self.assertTrue((ds_reg / "sql" / "01_raw_snowpipe.sql").exists())
        self.assertTrue((ds_reg / "sql" / "02_staging_dynamic_table.sql").exists())
        self.assertTrue((ds_reg / "sql" / "03_gold_dynamic_table.sql").exists())

    def test_4_step1_pauses_before_ddl_and_hierarchical_xml_e2e(self) -> None:
        """Verify Step 1 creates 3-layer YAMLs (NO DDL) before approval, and runs hierarchical XML E2E."""
        ent_sample_dir = Path(__file__).resolve().parent.parent / "datasets" / "enterprise_orders" / "samples"
        paused = run_full_onboarding_workflow(
            dataset="enterprise_orders",
            source_system="sap_s4hana",
            sample_dir=ent_sample_dir,
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/enterprise_orders/",
            auto_approve_gates=False,
        )
        self.assertEqual(paused["stage"], "PAUSED_AT_STAGE_3_C3_SCHEMA_REVIEW")
        ds_reg = self.registry_root / "enterprise_orders"
        self.assertTrue((ds_reg / "raw_schema.yaml").exists())
        self.assertTrue((ds_reg / "staging_schema.yaml").exists())
        self.assertTrue((ds_reg / "gold_schema.yaml").exists())
        self.assertTrue((ds_reg / "data_model.yaml").exists())
        self.assertFalse((ds_reg / "ddl.sql").exists())

        # Now run with approval enabled -> generates DDL (Step 2) -> deploys (Step 3) -> runs E2E
        live = run_full_onboarding_workflow(
            dataset="enterprise_orders",
            source_system="sap_s4hana",
            sample_dir=ent_sample_dir,
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/enterprise_orders/",
            auto_approve_gates=True,
        )
        self.assertEqual(live["status"], "PUBLISHED")
        self.assertTrue(live["smoke_test"]["smoke_test_passed"])
        self.assertEqual(live["smoke_test"]["curated_current_rows"], 5)
        self.assertTrue((ds_reg / "ddl.sql").exists())

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

    def test_5_final_deployment_to_snowflake_externalbrowser(self) -> None:
        """Verify final Go-Live connects to Snowflake using authenticator='externalbrowser' and deploys all 3 layers."""
        from unittest.mock import MagicMock, patch

        run_full_onboarding_workflow(
            dataset="orders",
            source_system="erp_orders",
            sample_dir=self.sample_dir,
            registry_root=self.registry_root,
            adls_landing_path="abfss://landing@adls.dfs.core.windows.net/xml/orders/",
            auto_approve_gates=True,
        )

        update_snowflake_config(
            {
                "mode": "externalbrowser",
                "authenticator": "externalbrowser",
                "account": "acme-enterprise.us-east-1",
                "user": "steward@enterprise.io",
                "role": "DATA_ENGINEER_ROLE",
                "warehouse": "COMPUTE_WH",
                "database": "ENTERPRISE_DW",
                "schema_raw": "RAW",
            }
        )

        executed_sqls: list[str] = []
        mock_cursor = MagicMock()
        mock_cursor.sfqid = "01b2c3d4-mock-qid"
        mock_cursor.rowcount = 1
        mock_cursor.fetchone.return_value = (
            "STEWARD@ENTERPRISE.IO",
            "DATA_ENGINEER_ROLE",
            "COMPUTE_WH",
            "ENTERPRISE_DW",
            "8.40.1",
            "ACME_ENTERPRISE",
        )

        def _capture_exec(sql: str, params=None):
            executed_sqls.append(sql.strip())

        mock_cursor.execute.side_effect = _capture_exec
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        import snowflake.connector

        with patch.object(snowflake.connector, "connect", return_value=mock_conn) as mock_connect:
            go_live_res = approve_c3_go_live(
                dataset="orders",
                registry_root=self.registry_root,
                deploy_to_snowflake=True,
            )

            # Verify externalbrowser authenticator was used
            mock_connect.assert_called_once()
            call_kwargs = mock_connect.call_args.kwargs
            self.assertEqual(call_kwargs["authenticator"], "externalbrowser")
            self.assertEqual(call_kwargs["account"], "acme-enterprise.us-east-1")
            self.assertEqual(call_kwargs["user"], "steward@enterprise.io")

        sf_dep = go_live_res["snowflake_live_deployment"]
        self.assertIsNotNone(sf_dep)
        self.assertTrue(sf_dep["deployed"])
        self.assertEqual(sf_dep["authenticator"], "externalbrowser")
        self.assertEqual(sf_dep["seeded_sample_files"], 10)
        self.assertTrue(sf_dep["snowpipe_enabled"])

        joined_sql = "\n".join(executed_sqls)
        self.assertIn("CREATE TABLE IF NOT EXISTS RAW.raw_orders", joined_sql)
        self.assertIn("CREATE PIPE IF NOT EXISTS RAW.pipe_orders", joined_sql)
        self.assertIn("CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_orders", joined_sql)
        self.assertIn("CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_orders", joined_sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS OPS.quarantine_orders", joined_sql)
        self.assertIn("ALTER PIPE IF EXISTS RAW.pipe_orders SET PIPE_EXECUTION_PAUSED = FALSE;", joined_sql)

        # Clean up runtime account override so other tests stay offline
        update_snowflake_config({"account": ""})


if __name__ == "__main__":
    unittest.main()
