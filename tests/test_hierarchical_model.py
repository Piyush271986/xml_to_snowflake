"""Unit and regression tests for hierarchical XML entity modeling."""
from pathlib import Path
import unittest
import yaml

from src.models import DatasetMapping
from src.entity_model import build_entity_model, render_er_diagram
from src.lookml_exporter import export_lookml_project
from src.schema_exporter import export_openapi_spec, export_json_schema
from src.hierarchical_dq import audit_xml_hierarchical_integrity
from src.agents.hierarchical_evolution import detect_new_child_entities
from src.drift_generator import generate_synthetic_xml
from src.reconciliation_auditor import run_reconciliation_audit
from src.schema_diff import compare_mappings, generate_changelog_markdown


class TestHierarchicalModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_dir = Path(__file__).resolve().parent.parent / "registry" / "analytics"
        mapping_path = cls.registry_dir / "mapping.yaml"
        cls.mapping = DatasetMapping.model_validate(yaml.safe_load(mapping_path.read_text(encoding="utf-8")))
        cls.entity_model = build_entity_model(cls.mapping)

    def test_entity_decomposition(self):
        """Verifies that all child and record entities are properly identified."""
        entity_names = {e.name for e in self.entity_model.entities}
        expected = {"assets", "asset", "country_classification", "cusip2", "cusip_alias"}
        self.assertTrue(expected.issubset(entity_names), f"Missing entities: {expected - entity_names}")

    def test_parent_child_relationships(self):
        """Verifies that child entities correctly reference the parent asset record."""
        by_name = {e.name: e for e in self.entity_model.entities}
        asset_ent = by_name["asset"]
        self.assertEqual(asset_ent.parent.name, "assets")

        for child_name in ["country_classification", "cusip2", "cusip_alias"]:
            child = by_name[child_name]
            self.assertIsNotNone(child.parent, f"{child_name} should have a parent")
            self.assertEqual(child.parent.name, "asset", f"{child_name} should reference asset")

    def test_reserved_keyword_escaping(self):
        """Verifies that SQL reserved words like CLASS are sanitized to class_val."""
        by_name = {e.name: e for e in self.entity_model.entities}
        asset_ent = by_name["asset"]
        col_names = {c.name for c in asset_ent.columns}
        self.assertIn("class_val", col_names)
        self.assertNotIn("class", col_names)

    def test_meramid_er_diagram_rendering(self):
        """Verifies that the Mermaid ER diagram is rendered with valid relationships."""
        diagram = render_er_diagram(self.entity_model, "STAGING")
        self.assertIn("erDiagram", diagram)
        self.assertIn("curated_analytics ||--o{ curated_analytics_asset", diagram)
        self.assertIn("curated_analytics_asset ||--o{ curated_analytics_cusip2", diagram)

    def test_openapi_spec_export(self):
        """Verifies OpenAPI export produces valid 3.1 specification."""
        test_out = self.registry_dir / "_test_openapi.json"
        try:
            spec = export_openapi_spec(self.entity_model, test_out)
            self.assertEqual(spec["openapi"], "3.1.0")
            self.assertIn("/api/v1/cusip2", spec["paths"])
            self.assertIn("cusip2", spec["components"]["schemas"])
        finally:
            if test_out.exists():
                test_out.unlink()
            json_schema_file = test_out.with_suffix(".json_schema.json")
            if json_schema_file.exists():
                json_schema_file.unlink()

    def test_hierarchical_dq_audit(self):
        """Verifies cardinality and size discrepancy auditing."""
        sample_file = Path(__file__).resolve().parent.parent / "samples" / "analytics" / "analytics.xml"
        if sample_file.exists():
            res = audit_xml_hierarchical_integrity(sample_file)
            self.assertTrue(res["passed"])
            self.assertEqual(res["size_discrepancies"], 0)
            self.assertEqual(res["average_cusip2_per_asset"], 5.0)

    def test_new_child_entity_evolution(self):
        """Verifies that an unseen repeating record set generates a child entity DDL proposal."""
        import tempfile
        xml_text = '''<?xml version="1.0" encoding="UTF-8"?>
<ASSETS>
    <ASSET>
        <BND_CORP>
            <CUSIP>1234AB5</CUSIP>
            <RATING_set SIZE="1">
                <RATING_record>
                    <AGENCY>MOODYS</AGENCY>
                    <RATING>Baa2</RATING>
                </RATING_record>
            </RATING_set>
        </BND_CORP>
    </ASSET>
</ASSETS>'''
        with tempfile.NamedTemporaryFile(suffix=".xml", mode="w", encoding="utf-8", delete=False) as tmp:
            tmp.write(xml_text)
            tmp_path = Path(tmp.name)
        try:
            proposals = detect_new_child_entities(tmp_path, self.mapping)
            self.assertEqual(len(proposals), 1)
            self.assertEqual(proposals[0].table_name, "staging_analytics_rating")
            self.assertIn("analytics_fk", proposals[0].staging_ddl)
        finally:
            tmp_path.unlink()

    def test_reconciliation_audit(self):
        """Verifies zero-loss reconciliation matches source count against curated store."""
        sample_file = Path(__file__).resolve().parent.parent / "samples" / "analytics" / "analytics.xml"
        if sample_file.exists():
            res = run_reconciliation_audit("analytics", sample_file, self.registry_dir.parent)
            self.assertTrue(res["reconciliation_matched"])
            self.assertEqual(res["metrics"]["discrepancy_delta"], 0)

    def test_schema_diff_and_changelog(self):
        """Verifies schema diff detects added fields and generates ALTER migration SQL."""
        import copy
        new_mapping = copy.deepcopy(self.mapping)
        new_mapping.version = "0.5.0"
        new_field = copy.deepcopy(new_mapping.fields[0])
        new_field.xpath = "/ASSETS/ASSET/BND_CORP/ESG_SCORE"
        new_field.column = "esg_score"
        new_field.snowflake_type = "NUMBER(3,0)"
        new_mapping.fields.append(new_field)

        diff = compare_mappings(self.mapping, new_mapping)
        self.assertEqual(len(diff.column_diffs), 1)
        self.assertEqual(diff.column_diffs[0].column, "esg_score")
        changelog = generate_changelog_markdown(diff)
        self.assertIn("v0.5.0", changelog)
        self.assertIn("ALTER DYNAMIC TABLE", changelog)

    def test_lookml_export(self):
        """Verifies LookML project export generates valid view files and an explore definition."""
        test_out = self.registry_dir / "_test_lookml"
        try:
            res = export_lookml_project(self.entity_model, test_out)
            self.assertEqual(res["views_count"], 5)
            self.assertTrue(Path(res["explore_file"]).exists())
            content = Path(res["explore_file"]).read_text(encoding="utf-8")
            self.assertIn("relationship: one_to_many", content)
        finally:
            import shutil
            if test_out.exists():
                shutil.rmtree(test_out)

    def test_synthetic_feed_generator(self):
        """Verifies synthetic feed generator creates valid XML structure."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xml", mode="w", encoding="utf-8", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            meta = generate_synthetic_xml(tmp_path, record_count=10, drift_mode="corrupt_size")
            self.assertEqual(meta["record_count"], 10)
            res = audit_xml_hierarchical_integrity(tmp_path)
            self.assertEqual(res["total_assets"], 10)
        finally:
            tmp_path.unlink()

    def test_reconciliation_audit(self):
        """Verifies zero-loss reconciliation matches source count against curated store."""
        sample_file = Path(__file__).resolve().parent.parent / "samples" / "analytics" / "analytics.xml"
        if sample_file.exists():
            res = run_reconciliation_audit("analytics", sample_file, self.registry_dir.parent)
            self.assertTrue(res["reconciliation_matched"])
            self.assertEqual(res["metrics"]["discrepancy_delta"], 0)

    def test_schema_diff_and_changelog(self):
        """Verifies schema diff detects added fields and generates ALTER migration SQL."""
        import copy
        new_mapping = copy.deepcopy(self.mapping)
        new_mapping.version = "0.5.0"
        new_field = copy.deepcopy(new_mapping.fields[0])
        new_field.xpath = "/ASSETS/ASSET/BND_CORP/ESG_SCORE"
        new_field.column = "esg_score"
        new_field.snowflake_type = "NUMBER(3,0)"
        new_mapping.fields.append(new_field)

        diff = compare_mappings(self.mapping, new_mapping)
        self.assertEqual(len(diff.column_diffs), 1)
        self.assertEqual(diff.column_diffs[0].column, "esg_score")
        changelog = generate_changelog_markdown(diff)
        self.assertIn("v0.5.0", changelog)
        self.assertIn("ALTER DYNAMIC TABLE", changelog)

    def test_lookml_export(self):
        """Verifies LookML project export generates valid view files and an explore definition."""
        test_out = self.registry_dir / "_test_lookml"
        try:
            res = export_lookml_project(self.entity_model, test_out)
            self.assertEqual(res["views_count"], 5)
            self.assertTrue(Path(res["explore_file"]).exists())
            content = Path(res["explore_file"]).read_text(encoding="utf-8")
            self.assertIn("relationship: one_to_many", content)
        finally:
            import shutil
            if test_out.exists():
                shutil.rmtree(test_out)


if __name__ == "__main__":
    unittest.main()
