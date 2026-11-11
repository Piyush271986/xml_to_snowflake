"""Unit tests for the Enterprise Alerting and Notification Dispatcher."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.alert_dispatcher import (
    AlertNotification,
    build_cardinality_alert,
    build_drift_alert,
    build_reconciliation_alert,
    dispatch_alert,
    format_pagerduty_payload,
    format_slack_blocks,
    format_teams_card,
)


class TestAlertDispatcher(unittest.TestCase):
    def test_build_reconciliation_alert(self):
        recon_failed = {
            "reconciliation_matched": False,
            "metrics": {
                "source_assets": 2191,
                "curated_assets": 2189,
                "quarantined_assets": 0,
                "discrepancy_delta": 2,
            },
        }
        alert = build_reconciliation_alert("analytics", recon_failed)
        self.assertEqual(alert.severity, "CRITICAL")
        self.assertEqual(alert.event_type, "RECONCILIATION_MISMATCH")
        self.assertIn("Delta = 2", alert.title)

    def test_build_cardinality_alert(self):
        dq_audit = {
            "xml_file": "analytics_broken.xml",
            "size_discrepancies": 3,
            "error_count": 3,
            "warning_count": 0,
            "findings_sample": [{"rule": "SIZE_MISMATCH"}],
        }
        alert = build_cardinality_alert("analytics", dq_audit)
        self.assertEqual(alert.severity, "HIGH")
        self.assertEqual(alert.event_type, "CARDINALITY_VIOLATION")
        self.assertIn("(3)", alert.title)

    def test_build_drift_alert(self):
        alert_breaking = build_drift_alert("analytics", "BREAKING_HELD_FOR_APPROVAL", 2, "broken.xml")
        self.assertEqual(alert_breaking.severity, "HIGH")
        self.assertEqual(alert_breaking.event_type, "BREAKING_DRIFT")

        alert_additive = build_drift_alert("analytics", "AUTO_APPLIED", 1, "additive.xml")
        self.assertEqual(alert_additive.severity, "INFO")
        self.assertEqual(alert_additive.event_type, "ADDITIVE_DRIFT")

    def test_payload_formatting(self):
        notif = AlertNotification(
            dataset="analytics",
            event_type="BREAKING_DRIFT",
            severity="CRITICAL",
            title="Critical Breaking Drift in Feed",
            summary="Missing required tag",
            details={"column": "CUSIP"},
        )

        slack = format_slack_blocks(notif)
        self.assertIn("blocks", slack)
        self.assertEqual(slack["blocks"][0]["text"]["text"], "🚨 Critical Breaking Drift in Feed")

        teams = format_teams_card(notif)
        self.assertEqual(teams["@type"], "MessageCard")
        self.assertEqual(teams["themeColor"], "d9534f")

        pd = format_pagerduty_payload(notif)
        self.assertEqual(pd["payload"]["severity"], "critical")
        self.assertEqual(pd["payload"]["group"], "analytics")

    def test_dispatch_and_history_logging(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            reg_root = Path(tmp_dir)
            ds_dir = reg_root / "analytics"
            ds_dir.mkdir()

            notif = AlertNotification(
                dataset="analytics",
                event_type="RECONCILIATION_MISMATCH",
                severity="CRITICAL",
                title="Audit Balance Mismatch",
                summary="Delta = 5",
                details={"delta": 5},
            )

            res = dispatch_alert(notif, dry_run=True, registry_root=reg_root)
            self.assertEqual(res["status"], "SENT")
            self.assertEqual(res["dispatch_code"], "DRY_RUN_DISPATCHED")

            history_file = ds_dir / "alert_history.jsonl"
            self.assertTrue(history_file.exists())
            logged = json.loads(history_file.read_text().strip())
            self.assertEqual(logged["title"], "Audit Balance Mismatch")


if __name__ == "__main__":
    unittest.main()
