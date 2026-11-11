"""Unit test wrapper for dbt-style referential integrity and uniqueness assertions."""
from __future__ import annotations

import unittest
from scripts.verify_dbt_referential_integrity import run_dbt_style_assertions


class TestDbtReferentialIntegrity(unittest.TestCase):
    def test_referential_integrity_and_uniqueness(self):
        res = run_dbt_style_assertions(dataset="analytics")
        self.assertTrue(res["passed"], "dbt-style integrity assertions failed")
        self.assertEqual(res["cusip2_orphans"], 0)
        self.assertEqual(res["cc_orphans"], 0)
        self.assertEqual(res["alias_orphans"], 0)


if __name__ == "__main__":
    unittest.main()
