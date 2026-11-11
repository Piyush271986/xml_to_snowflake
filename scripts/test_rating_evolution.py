import yaml
from pathlib import Path
from src.models import DatasetMapping
from src.agents.hierarchical_evolution import detect_new_child_entities

test_xml = Path("samples/analytics_drift/analytics_rating_drift.xml")
test_xml.write_text(
    """<?xml version="1.0" encoding="UTF-8"?>
<ASSETS ASOF_DATE="5/11/2026" CREATE_DATE="5/11/2026" RECORDS="1">
  <ASSET>
    <BND_CORP>
      <ACCRUAL_DT>1/22/2024</ACCRUAL_DT>
      <AMT_ISU>525000000</AMT_ISU>
      <COUNTRY>GB</COUNTRY>
      <RATING_set SIZE="2">
        <RATING_record>
          <AGENCY>MOODYS</AGENCY>
          <RATING>Baa1</RATING>
          <RATING_DATE>2026-01-15</RATING_DATE>
        </RATING_record>
        <RATING_record>
          <AGENCY>SP</AGENCY>
          <RATING>BBB+</RATING>
          <RATING_DATE>2026-02-01</RATING_DATE>
        </RATING_record>
      </RATING_set>
    </BND_CORP>
  </ASSET>
</ASSETS>""",
    encoding="utf-8",
)

with open("registry/analytics/mapping.yaml", "r", encoding="utf-8") as f:
    mapping = DatasetMapping(**yaml.safe_load(f))

proposals = detect_new_child_entities(test_xml, mapping)
print(f"Proposals detected: {len(proposals)}")
for p in proposals:
    print("--- New Child Entity Proposal ---")
    print(f"Container Tag: {p.container_tag}")
    print(f"Record Tag:    {p.record_tag}")
    print(f"Entity Name:   {p.entity_name}")
    print(f"Staging Table: {p.table_name}")
    print("Columns extracted:")
    for c in p.columns:
        print(f"  • {c['name']} ({c['type']})")
    print("\nCompiled Staging DDL:")
    print(p.staging_ddl)
    print("\nCompiled Curated DDL:")
    print(p.curated_ddl)
