"""Stage 5 — A2: Catalog Agent.

Registers all Snowflake tables in DataHub, attaches table & column-level lineage
(ADLS -> D2 Raw -> D3 Staging -> D4 Curated), links contract.yaml, and tags owners & SLAs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.models import DatasetMapping, OnboardingManifest


def run_a2_catalog(dataset: str, registry_root: Path, env: str = "PROD") -> dict[str, Any]:
    """Emit DataHub entities, lineage graph, contracts, and ownership metadata."""
    ds_registry = registry_root / dataset
    manifest = OnboardingManifest.model_validate(
        yaml.safe_load((ds_registry / "onboarding_manifest.yaml").read_text(encoding="utf-8"))
    )
    mapping = DatasetMapping.model_validate(
        yaml.safe_load((ds_registry / "mapping.yaml").read_text(encoding="utf-8"))
    )

    def make_urn(table_name: str) -> str:
        return f"urn:li:dataset:(urn:li:dataPlatform:snowflake,{table_name},{env})"

    adls_urn = f"urn:li:dataset:(urn:li:dataPlatform:adls,{manifest.adls_landing_path.strip('/')},{env})"
    raw_urn = make_urn(mapping.targets.raw_table)
    stg_urn = make_urn(mapping.targets.staging_table)
    cur_urn = make_urn(mapping.targets.curated_table)
    quar_urn = make_urn(mapping.targets.quarantine_table)

    column_lineage = [
        {
            "xpath": f.xpath,
            "staging_column": f"{stg_urn}#{f.column}",
            "curated_column": f"{cur_urn}#{f.column}",
            "snowflake_type": f.snowflake_type,
        }
        for f in mapping.fields
    ]

    catalog_payload = {
        "dataset": dataset,
        "status": "PROVISIONED",
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "owners": {
            "data_steward": manifest.data_steward,
            "data_engineering": manifest.engineering_owner,
            "platform_oncall": manifest.platform_oncall,
        },
        "sla_tags": {
            "freshness_sla_hours": manifest.freshness_sla_hours,
            "cdc_mode": "SCD_TYPE_2",
        },
        "entities": {
            "adls_landing": adls_urn,
            "d2_raw": raw_urn,
            "d3_staging": stg_urn,
            "d4_curated": cur_urn,
            "o3_quarantine": quar_urn,
        },
        "upstream_lineage": [
            {"upstream": adls_urn, "downstream": raw_urn, "mechanism": f"Snowpipe (pipe_{dataset})"},
            {"upstream": raw_urn, "downstream": stg_urn, "mechanism": f"Stream + Task (task_flatten_{dataset})"},
            {"upstream": stg_urn, "downstream": cur_urn, "mechanism": f"SCD Type 2 Merge (task_scd2_{dataset})"},
        ],
        "column_lineage": column_lineage,
        "attached_contract": str(ds_registry / "contract.yaml"),
    }

    (ds_registry / "datahub_urns.yaml").write_text(
        yaml.safe_dump(catalog_payload, sort_keys=False),
        encoding="utf-8",
    )

    manifest.status = "PROVISIONED"
    (ds_registry / "onboarding_manifest.yaml").write_text(
        yaml.safe_dump(manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    return catalog_payload
