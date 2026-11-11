"""Unit and integration tests for Prometheus metrics collection and /metrics endpoint."""
from __future__ import annotations

import unittest
from starlette.testclient import TestClient

from src.metrics_collector import collect_pipeline_metrics, format_prometheus_metrics
from src.web_app import app


class TestMetricsCollector(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dataset = "analytics"

    def test_collect_pipeline_metrics(self):
        metrics = collect_pipeline_metrics(dataset=self.dataset)
        self.assertEqual(metrics["dataset"], self.dataset)
        self.assertIn("source_assets", metrics)
        self.assertIn("curated_assets", metrics)
        self.assertIn("quarantined_assets", metrics)
        self.assertIn("reconciliation_delta", metrics)
        self.assertIn("cusip2_records", metrics)
        self.assertGreaterEqual(metrics["source_assets"], 0)

    def test_format_prometheus_metrics(self):
        sample_metrics = {
            "dataset": "analytics",
            "source_assets": 2191,
            "curated_assets": 2191,
            "quarantined_assets": 0,
            "reconciliation_delta": 0,
            "reconciliation_matched": 1,
            "size_discrepancies": 0,
            "cusip2_records": 10955,
            "country_classification_records": 4382,
            "cusip_alias_records": 2191,
            "warehouse_rows": {"raw": 1, "staging": 2191, "curated": 2191, "quarantine": 0},
        }
        prom_text = format_prometheus_metrics(sample_metrics)
        self.assertIn("# HELP xml_pipeline_source_records_total", prom_text)
        self.assertIn('xml_pipeline_source_records_total{dataset="analytics"} 2191', prom_text)
        self.assertIn('xml_pipeline_reconciliation_delta{dataset="analytics"} 0', prom_text)
        self.assertIn('xml_pipeline_child_records_total{dataset="analytics",entity="cusip2"} 10955', prom_text)

    def test_metrics_api_endpoint(self):
        resp = self.client.get(f"/api/metrics?dataset={self.dataset}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/plain", resp.headers["content-type"])
        self.assertIn("xml_pipeline_source_records_total", resp.text)

    def test_metrics_root_alias(self):
        resp = self.client.get("/metrics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("xml_pipeline_curated_records_total", resp.text)


if __name__ == "__main__":
    unittest.main()
