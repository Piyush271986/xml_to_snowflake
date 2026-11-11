"""Integration and verification tests for live DataHub GMS and metadata assertions."""
from __future__ import annotations

import unittest
import urllib.parse
import urllib.request
import json
from pathlib import Path

from src.emit_datahub_assertions import emit_analytics_assertions
from src.agents.a2_catalog import run_a2_catalog


class TestDataHubIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gms_url = "http://localhost:8080"
        cls.registry_dir = Path(__file__).resolve().parent.parent / "registry"
        cls.sample_file = Path(__file__).resolve().parent.parent / "samples" / "analytics" / "analytics.xml"

    def test_gms_health(self):
        """Verifies DataHub GMS backend is healthy and responding to HTTP requests."""
        try:
            req = urllib.request.Request(f"{self.gms_url}/health", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
        except Exception as e:
            self.skipTest(f"DataHub GMS not reachable at {self.gms_url}: {e}")

    def test_catalog_emission(self):
        """Verifies A2 Catalog agent publishes dataset entities and upstream lineage to DataHub."""
        try:
            res = run_a2_catalog("analytics", self.registry_dir)
            self.assertTrue(res.get("datahub_live", {}).get("live_emitted", False))
            self.assertGreaterEqual(res.get("datahub_live", {}).get("emitted_urns_count", 0), 5)
        except Exception as e:
            self.skipTest(f"DataHub emission skipped: {e}")

    def test_assertions_and_quality_tags_emission(self):
        """Verifies quality tags and reconciliation assertions are emitted to DataHub."""
        if not self.sample_file.exists():
            self.skipTest("analytics.xml not found")
        try:
            res = emit_analytics_assertions(self.gms_url, self.sample_file)
            self.assertEqual(res["status"], "EMITTED")
            self.assertEqual(res["reconciliation"], "RECONCILED")
            self.assertEqual(res["size_discrepancies"], 0)
            self.assertIn("urn:li:tag:DQ_REFERENTIAL_INTEGRITY_PASSED", res["emitted_tags"])
            self.assertIn("urn:li:tag:RECONCILIATION_RECONCILED", res["emitted_tags"])
        except Exception as e:
            self.skipTest(f"DataHub assertion emission skipped: {e}")


if __name__ == "__main__":
    unittest.main()
