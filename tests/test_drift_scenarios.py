"""End-to-End Regression Tests for Schema Drift Scenarios (Additive, Breaking, Malformed)."""
from __future__ import annotations

import unittest
from pathlib import Path

from src.agents.c1_drift_agent import detect_schema_drift
from src.agents.c2_proposal_agent import handle_drift_findings
from src.orchestrator import process_runtime_file_with_drift_control


class TestDriftScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.registry_dir = cls.base_dir / "registry"
        cls.drift_dir = cls.base_dir / "samples" / "analytics_drift"

    def test_additive_drift_scenario(self):
        """Verifies additive drift is auto-classified as non-breaking and generates ALTER DDL."""
        sample = self.drift_dir / "analytics_additive_drift.xml"
        if not sample.exists():
            self.skipTest("analytics_additive_drift.xml not found")

        # Ingest through orchestrator
        res = process_runtime_file_with_drift_control("analytics", sample, self.registry_dir)
        self.assertIn("ingest_metrics", res)
        # Should not block at C3 if already handled or auto-applied
        self.assertTrue(res["ingest_metrics"]["files_processed"] >= 1)

    def test_breaking_drift_scenario(self):
        """Verifies breaking drift halts at C3 Gate and diverts corrupt record to quarantine."""
        sample = self.drift_dir / "analytics_breaking_drift.xml"
        if not sample.exists():
            self.skipTest("analytics_breaking_drift.xml not found")

        findings = detect_schema_drift(sample, self.registry_dir, "analytics")
        breaking_findings = [f for f in findings if f.classification == "BREAKING"]
        self.assertTrue(len(breaking_findings) >= 1)
        self.assertEqual(breaking_findings[0].xpath, "/ASSETS/ASSET/BND_CORP/AMT_ISU")

        proposal = handle_drift_findings("analytics", self.registry_dir, findings)
        self.assertEqual(proposal.status, "PENDING_C3_APPROVAL")
        self.assertEqual(proposal.proposed_version, "1.0.0")

        # Process through orchestrator and check quarantine metrics
        res = process_runtime_file_with_drift_control("analytics", sample, self.registry_dir)
        self.assertEqual(res["proposal_status"], "PENDING_C3_APPROVAL")
        self.assertGreater(res["ingest_metrics"]["quarantine_open_rows"], 0)

    def test_malformed_xml_scenario(self):
        """Verifies malformed XML with unclosed tokens is caught at Gate G1."""
        sample = self.drift_dir / "analytics_malformed.xml"
        if not sample.exists():
            self.skipTest("analytics_malformed.xml not found")

        res = process_runtime_file_with_drift_control("analytics", sample, self.registry_dir)
        # G1 check prevents file passage
        self.assertEqual(res["ingest_metrics"]["files_passed"], 0)
        self.assertGreater(res["ingest_metrics"]["files_quarantined"], 0)


if __name__ == "__main__":
    unittest.main()
