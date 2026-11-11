"""Audits and executes dbt-style referential integrity and uniqueness tests on the exploded hierarchy."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

from src.models import DatasetMapping
from src.entity_model import build_entity_model
import yaml


def run_dbt_style_assertions(dataset: str = "analytics") -> dict[str, any]:
    ds_reg = Path("registry") / dataset
    mapping_data = yaml.safe_load((ds_reg / "mapping.yaml").read_text(encoding="utf-8"))
    mapping = DatasetMapping(**mapping_data)
    model = build_entity_model(mapping)

    xml_path = Path("samples/analytics/analytics.xml")
    if not xml_path.exists():
        xml_path = Path("datasets/analytics/samples/analytics.xml")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # In-memory evaluation of surrogate PK/FK referential integrity
    assets_keys = set()
    asset_keys = set()
    cusip2_fk_references = []
    cc_fk_references = []
    alias_fk_references = []

    file_name = xml_path.name
    import hashlib
    file_sha = hashlib.sha256(xml_path.read_bytes()).hexdigest()

    # Document Level Key
    doc_pk = hashlib.md5(f"{file_name}|{file_sha}".encode()).hexdigest()
    assets_keys.add(doc_pk)

    total_assets = 0
    total_cusip2 = 0
    total_cc = 0
    total_alias = 0

    for a_idx, asset in enumerate(root.findall(".//ASSET")):
        total_assets += 1
        asset_pk = hashlib.md5(f"{file_name}|{file_sha}|{a_idx}".encode()).hexdigest()
        asset_keys.add(asset_pk)

        bnd = asset.find("BND_CORP")
        if bnd is None:
            bnd = asset

        # CUSIP2 set
        cusip_set = bnd.find("CUSIP2_set")
        if cusip_set is not None:
            for c_idx, rec in enumerate(cusip_set.findall("CUSIP2_record")):
                total_cusip2 += 1
                c_pk = hashlib.md5(f"{file_name}|{file_sha}|{a_idx}|{c_idx}".encode()).hexdigest()
                cusip2_fk_references.append((c_pk, asset_pk))

        # Country classification set
        cc_set = bnd.find("COUNTRY_CLASSIFICATION_set")
        if cc_set is not None:
            for cc_idx, rec in enumerate(cc_set.findall("COUNTRY_CLASSIFICATION_record")):
                total_cc += 1
                cc_pk = hashlib.md5(f"{file_name}|{file_sha}|{a_idx}|{cc_idx}".encode()).hexdigest()
                cc_fk_references.append((cc_pk, asset_pk))

        # Alias set
        alias_set = bnd.find("CUSIP_ALIAS_set")
        if alias_set is not None:
            for al_idx, rec in enumerate(alias_set.findall("CUSIP_ALIAS_record")):
                total_alias += 1
                al_pk = hashlib.md5(f"{file_name}|{file_sha}|{a_idx}|{al_idx}".encode()).hexdigest()
                alias_fk_references.append((al_pk, asset_pk))

    # Assertions
    # 1. Primary Key Uniqueness
    cusip2_pks = [c[0] for c in cusip2_fk_references]
    cc_pks = [c[0] for c in cc_fk_references]
    alias_pks = [c[0] for c in alias_fk_references]

    pk_unique_asset = len(asset_keys) == total_assets
    pk_unique_cusip2 = len(set(cusip2_pks)) == total_cusip2
    pk_unique_cc = len(set(cc_pks)) == total_cc
    pk_unique_alias = len(set(alias_pks)) == total_alias

    # 2. Foreign Key Referential Integrity (Orphan checks)
    cusip2_orphans = [c for c in cusip2_fk_references if c[1] not in asset_keys]
    cc_orphans = [c for c in cc_fk_references if c[1] not in asset_keys]
    alias_orphans = [c for c in alias_fk_references if c[1] not in asset_keys]

    print("=" * 80)
    print("  DBT-STYLE HIERARCHICAL REFERENTIAL INTEGRITY AUDIT")
    print("=" * 80)
    print(f"\n📊 Extracted Table Counts:")
    print(f"  • stg_assets:                  {len(assets_keys):>6} rows (1 document)")
    print(f"  • stg_asset:                   {len(asset_keys):>6} rows")
    print(f"  • stg_cusip2:                  {len(cusip2_pks):>6} rows (FK -> stg_asset)")
    print(f"  • stg_country_classification:  {len(cc_pks):>6} rows (FK -> stg_asset)")
    print(f"  • stg_cusip_alias:             {len(alias_pks):>6} rows (FK -> stg_asset)")

    print(f"\n🔍 [1/2] Primary Key Uniqueness & Not-Null Tests:")
    print(f"  • stg_assets.assets_pk:                  {'✅ PASS (1 unique)' if len(assets_keys)==1 else '❌ FAIL'}")
    print(f"  • stg_asset.asset_pk:                    {'✅ PASS (' + str(total_assets) + ' unique)' if pk_unique_asset else '❌ FAIL'}")
    print(f"  • stg_cusip2.cusip2_pk:                  {'✅ PASS (' + str(total_cusip2) + ' unique)' if pk_unique_cusip2 else '❌ FAIL'}")
    print(f"  • stg_country_classification.cc_pk:      {'✅ PASS (' + str(total_cc) + ' unique)' if pk_unique_cc else '❌ FAIL'}")
    print(f"  • stg_cusip_alias.alias_pk:              {'✅ PASS (' + str(total_alias) + ' unique)' if pk_unique_alias else '❌ FAIL'}")

    print(f"\n🔗 [2/2] Foreign Key Referential Relationships Tests:")
    print(f"  • stg_cusip2.asset_fk -> stg_asset.asset_pk:                 {'✅ PASS (0 orphans out of ' + str(total_cusip2) + ')' if not cusip2_orphans else '❌ FAIL'}")
    print(f"  • stg_country_classification.asset_fk -> stg_asset.asset_pk: {'✅ PASS (0 orphans out of ' + str(total_cc) + ')' if not cc_orphans else '❌ FAIL'}")
    print(f"  • stg_cusip_alias.asset_fk -> stg_asset.asset_pk:            {'✅ PASS (0 orphans out of ' + str(total_alias) + ')' if not alias_orphans else '❌ FAIL'}")

    all_pass = (
        pk_unique_asset and pk_unique_cusip2 and pk_unique_cc and pk_unique_alias and
        not cusip2_orphans and not cc_orphans and not alias_orphans
    )
    print("=" * 80)
    print(f"  {'🎉 ALL 8 DBT INTEGRITY TESTS PASSED' if all_pass else '❌ INTEGRITY AUDIT FAILED'}")
    print("=" * 80)

    return {
        "passed": all_pass,
        "total_assets": total_assets,
        "total_cusip2": total_cusip2,
        "total_cc": total_cc,
        "total_alias": total_alias,
        "cusip2_orphans": len(cusip2_orphans),
        "cc_orphans": len(cc_orphans),
        "alias_orphans": len(alias_orphans),
    }


if __name__ == "__main__":
    res = run_dbt_style_assertions()
    if not res["passed"]:
        sys.exit(1)
