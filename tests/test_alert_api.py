"""Integration tests for the Alert Feed & Incident Management API."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from starlette.testclient import TestClient

from src.web_app import app


class TestAlertAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dataset = "analytics"

    def test_get_alerts_endpoint(self):
        resp = self.client.get(f"/api/alerts?dataset={self.dataset}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("dataset"), self.dataset)
        self.assertIsInstance(data.get("alerts"), list)

    def test_send_test_alert_endpoint(self):
        resp = self.client.post(
            "/api/alerts/test",
            json={"dataset": self.dataset, "severity": "HIGH"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("result", {}).get("status"), "SENT")

        # Verify alert now appears in GET /api/alerts
        get_resp = self.client.get(f"/api/alerts?dataset={self.dataset}")
        self.assertEqual(get_resp.status_code, 200)
        get_data = get_resp.json()
        self.assertGreaterEqual(get_data.get("count", 0), 1)
        self.assertEqual(get_data["alerts"][0]["severity"], "HIGH")


if __name__ == "__main__":
    unittest.main()
