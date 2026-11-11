"""Hierarchical Schema Evolution Agent.

Detects when an incoming XML batch introduces brand-new repeating child sets
(e.g., <RATING_set> -> <RATING_record>) and generates the non-breaking
Snowflake Dynamic Table DDL and mapping updates needed to explode the new child entity.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from src.entity_model import build_entity_model
from src.models import DatasetMapping, FieldMapping
from src.xml_infer import (
    extract_xml_xpaths_and_values,
    resolve_narrowest_snowflake_type,
    to_snake_case,
)


@dataclass
class NewChildEntityProposal:
    container_tag: str
    record_tag: str
    entity_name: str
    table_name: str
    parent_table: str
    columns: list[dict[str, str]]
    staging_ddl: str
    curated_ddl: str


def detect_new_child_entities(
    xml_file: Path,
    mapping: DatasetMapping,
) -> list[NewChildEntityProposal]:
    """Scans an XML file for repeating record containers not currently mapped in mapping.yaml."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    known_xpaths = {f.xpath for f in mapping.fields}
    proposals: list[NewChildEntityProposal] = []

    # Find candidate repeating record sets inside ASSET / record elements
    for asset in root.findall(".//ASSET"):
        parent_container = asset.find("BND_CORP")
        if parent_container is None:
            parent_container = asset

        for child_elem in list(parent_container):
            tag = child_elem.tag
            # Structural repeating containers usually end in _set or have a SIZE attribute
            if tag.endswith("_set") or "SIZE" in child_elem.attrib:
                records = [c for c in list(child_elem) if c.tag.endswith("_record") or c.tag.endswith("_item")]
                if records:
                    first_record = records[0]
                    record_tag = first_record.tag
                    sample_xpath = f"/{root.tag}/ASSET/{parent_container.tag}/{tag}/{record_tag}"

                    # If this XPath pattern is not in our known field inventory, it's a new child entity
                    is_known = any(f.xpath.startswith(sample_xpath) for f in mapping.fields)
                    if not is_known and not any(p.container_tag == tag for p in proposals):
                        entity_base = to_snake_case(record_tag.replace("_record", "").replace("_item", ""))
                        entity_name = f"{mapping.dataset}_{entity_base}"
                        staging_tbl = f"staging_{entity_name}"
                        curated_tbl = f"curated_{entity_name}"
                        parent_tbl = f"staging_{mapping.dataset}"

                        # Extract columns from sample child record
                        cols: list[dict[str, str]] = []
                        for leaf in list(first_record):
                            leaf_name = to_snake_case(leaf.tag)
                            leaf_val = leaf.text.strip() if leaf.text else ""
                            sf_type = resolve_narrowest_snowflake_type([leaf_val]) if leaf_val else "VARCHAR(64)"
                            cols.append({
                                "tag": leaf.tag,
                                "name": leaf_name,
                                "type": sf_type,
                            })

                        # Compile Staging Dynamic Table SQL
                        col_selects = ",\n".join(
                            f"    c.value:{c['tag']}::{c['type']:<20} AS {c['name']}"
                            for c in cols
                        )
                        stg_sql = f"""CREATE OR REPLACE DYNAMIC TABLE ENTERPRISE_DW.STAGING.{staging_tbl.upper()}
  TARGET_LAG = '1 minute'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a.index, c.index)) AS {entity_base}_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a.index))          AS {mapping.dataset}_fk,
{col_selects}
FROM ENTERPRISE_DW.RAW.RAW_{mapping.dataset.upper()} r,
     LATERAL FLATTEN(input => r.raw_payload:"$") a,
     LATERAL FLATTEN(input => a.value:{parent_container.tag}.{tag}:"$") c
WHERE a.value['#name'] = 'ASSET'
  AND c.value['#name'] = '{record_tag}';"""

                        # Compile Curated Dynamic Table SQL
                        cur_sql = f"""CREATE OR REPLACE DYNAMIC TABLE ENTERPRISE_DW.CURATED.{curated_tbl.upper()}
  TARGET_LAG = '5 minutes'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
    c.{entity_base}_pk,
    c.{mapping.dataset}_fk,
    {', '.join([f'c.{c["name"]}' for c in cols])}
FROM ENTERPRISE_DW.STAGING.{staging_tbl.upper()} c
JOIN ENTERPRISE_DW.CURATED.CURATED_{mapping.dataset.upper()} p
  ON c.{mapping.dataset}_fk = p.{mapping.dataset}_pk;"""

                        proposals.append(
                            NewChildEntityProposal(
                                container_tag=tag,
                                record_tag=record_tag,
                                entity_name=entity_name,
                                table_name=staging_tbl,
                                parent_table=parent_tbl,
                                columns=cols,
                                staging_ddl=stg_sql,
                                curated_ddl=cur_sql,
                            )
                        )

    return proposals
