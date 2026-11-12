"""Integration tests for dynamic child entity approval and auto-DDL regeneration."""
from __future__ import annotations

import json
from pathlib import Path
import unittest
import yaml

from starlette.testclient import TestClient

from src.models import DatasetMapping
from src.web_app import app

REGISTRY_ROOT = Path("registry")


class TestChildEntityApproval(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dataset = "analytics"
        self.ds_dir = REGISTRY_ROOT / self.dataset
        self.backup_mapping = (self.ds_dir / "mapping.yaml").read_text(encoding="utf-8")
        self.backup_ddl = (self.ds_dir / "ddl.sql").read_text(encoding="utf-8")
        self.backup_data_model = (self.ds_dir / "data_model.yaml").read_text(encoding="utf-8")

    def tearDown(self):
        # Restore backups to maintain clean state
        (self.ds_dir / "mapping.yaml").write_text(self.backup_mapping, encoding="utf-8")
        (self.ds_dir / "ddl.sql").write_text(self.backup_ddl, encoding="utf-8")
        (self.ds_dir / "data_model.yaml").write_text(self.backup_data_model, encoding="utf-8")

    def test_approve_child_entity_workflow(self):
        proposal = {
            "container_tag": "RATING_set",
            "record_tag": "RATING_record",
            "entity_name": "analytics_rating",
            "table_name": "staging_analytics_rating",
            "columns": [
                {"name": "agency", "tag": "AGENCY", "type": "VARCHAR(64)"},
                {"name": "rating", "tag": "RATING", "type": "VARCHAR(16)"},
                {"name": "rating_date", "tag": "RATING_DATE", "type": "DATE"},
            ],
            "staging_ddl": "-- mock",
            "curated_ddl": "-- mock",
        }

        resp = self.client.post(
            "/api/approve-child-entity",
            json={"dataset": self.dataset, "proposal": proposal},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("entity_name"), "rating")
        self.assertIn("agency", data.get("added_fields"))

        # Verify mapping.yaml contains the new fields
        updated_mapping = yaml.safe_load((self.ds_dir / "mapping.yaml").read_text(encoding="utf-8"))
        rating_fields = [f for f in updated_mapping["fields"] if "RATING_record" in f["xpath"]]
        self.assertEqual(len(rating_fields), 3)

        # Verify master ddl.sql contains the new dynamic table
        updated_ddl = (self.ds_dir / "ddl.sql").read_text(encoding="utf-8")
        self.assertIn("staging_analytics_rating", updated_ddl.lower())


if __name__ == "__main__":
    unittest.main()
