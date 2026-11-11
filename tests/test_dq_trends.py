"""Unit and integration tests for Data Quality Trends and Health Score analyzer."""
from __future__ import annotations

import unittest
from starlette.testclient import TestClient

from src.dq_trends_analyzer import analyze_quality_trends
from src.web_app import app


class TestDqTrends(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dataset = "analytics"

    def test_analyze_quality_trends_structure(self):
        res = analyze_quality_trends(self.dataset)
        self.assertEqual(res["dataset"], self.dataset)
        self.assertIn("health_score", res)
        self.assertIn("health_status", res)
        self.assertIn("layer_counts", res)
        self.assertIn("alert_summary", res)
        self.assertIn("trend_points", res)
        self.assertGreaterEqual(res["health_score"], 0)
        self.assertLessEqual(res["health_score"], 100)
        self.assertEqual(len(res["trend_points"]), 7)

    def test_dq_trends_api_endpoint(self):
        resp = self.client.get(f"/api/dq/trends?dataset={self.dataset}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("dataset"), self.dataset)
        self.assertIsInstance(data.get("trend_points"), list)


if __name__ == "__main__":
    unittest.main()
