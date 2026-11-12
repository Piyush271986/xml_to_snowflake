"""Stage 5 — A2: Catalog Agent.

Registers all Snowflake tables in DataHub (both local registry YAML and live DataHub GMS REST API
at http://localhost:8080), attaches table & column-level lineage (ADLS -> RAW -> Stage Dynamic Table -> Gold Dynamic Table),
links contract.yaml, and tags owners & SLAs.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any

import yaml

from src.entity_model import build_entity_model
from src.models import DatasetMapping, OnboardingManifest

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"


def _load_datahub_settings() -> dict[str, Any]:
    if DEFAULT_SETTINGS_PATH.exists():
        try:
            cfg = yaml.safe_load(DEFAULT_SETTINGS_PATH.read_text(encoding="utf-8")) or {}
            return cfg.get("datahub") or {}
        except Exception:
            pass
    return {"mode": "rest", "gms_server": "http://localhost:8080", "ui_url": "http://localhost:9002", "env": "PROD"}


def _emit_to_live_datahub(
    gms_server: str,
    dataset: str,
    manifest: OnboardingManifest,
    mapping: DatasetMapping,
    entities: dict[str, str],
) -> dict[str, Any]:
    """Emit dataset properties, schemas, ownership, tags, and upstream lineage to live DataHub GMS."""
    from datahub.emitter.mcp import MetadataChangeProposalWrapper
    from datahub.emitter.rest_emitter import DatahubRestEmitter
    from datahub.metadata.schema_classes import (
        AuditStampClass,
        DatasetLineageTypeClass,
        DatasetPropertiesClass,
        GlobalTagsClass,
        NumberTypeClass,
        OtherSchemaClass,
        OwnerClass,
        OwnershipClass,
        OwnershipTypeClass,
        SchemaFieldClass,
        SchemaFieldDataTypeClass,
        SchemaMetadataClass,
        StringTypeClass,
        TagAssociationClass,
        TimeTypeClass,
        BooleanTypeClass,
        UpstreamClass,
        UpstreamLineageClass,
    )

    emitter = DatahubRestEmitter(gms_server=gms_server, connect_timeout_sec=4, read_timeout_sec=8)
    emitter.test_connection()

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    audit_stamp = AuditStampClass(time=now_ms, actor="urn:li:corpuser:datahub")

    owners = [
        OwnerClass(owner=f"urn:li:corpuser:{manifest.data_steward}", type=OwnershipTypeClass.DATAOWNER),
        OwnerClass(owner=f"urn:li:corpuser:{manifest.engineering_owner}", type=OwnershipTypeClass.TECHNICAL_OWNER),
    ]
    ownership = OwnershipClass(owners=owners, lastModified=audit_stamp)

    tags = GlobalTagsClass(
        tags=[
            TagAssociationClass(tag=f"urn:li:tag:SLA_{manifest.freshness_sla_hours}h"),
            TagAssociationClass(tag="urn:li:tag:XML_Onboarding_Pipeline"),
            TagAssociationClass(tag="urn:li:tag:Snowflake_Dynamic_Table"),
        ]
    )

    def _sf_to_dh_type(sf_type: str) -> SchemaFieldDataTypeClass:
        u = sf_type.upper()
        if u.startswith("NUMBER") or u.startswith("INT") or u.startswith("DECIMAL"):
            return SchemaFieldDataTypeClass(type=NumberTypeClass())
        if u in ("DATE", "TIMESTAMP_NTZ", "TIMESTAMP"):
            return SchemaFieldDataTypeClass(type=TimeTypeClass())
        if u == "BOOLEAN":
            return SchemaFieldDataTypeClass(type=BooleanTypeClass())
        return SchemaFieldDataTypeClass(type=StringTypeClass())

    emitted_urns: list[str] = []

    # 1. Emit properties, ownership, tags & schema for each dataset entity
    entity_descriptions = {
        "adls_landing": (
            f"ADLS Landing Zone ({manifest.adls_landing_path})",
            "D1: Azure Data Lake Storage Gen2 XML landing directory monitored by Snowpipe.",
            [
                SchemaFieldClass(
                    fieldPath="xml_payload",
                    type=SchemaFieldDataTypeClass(type=StringTypeClass()),
                    nativeDataType="XML",
                    description="Raw XML file in ADLS landing zone",
                )
            ],
        ),
        "d2_raw": (
            f"RAW.{mapping.targets.raw_table}",
            f"Layer 1 (RAW Normal Table): Immutable XML payload loaded idempotently from ADLS via Snowpipe (pipe_{dataset}).",
            [
                SchemaFieldClass(fieldPath="_file_name", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(512)", description="Source XML file name"),
                SchemaFieldClass(fieldPath="_file_sha256", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(64)", description="SHA-256 hash"),
                SchemaFieldClass(fieldPath="_source_system", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(128)", description="Upstream source system"),
                SchemaFieldClass(fieldPath="_ingestion_ts", type=SchemaFieldDataTypeClass(type=TimeTypeClass()), nativeDataType="TIMESTAMP_NTZ", description="Snowpipe load timestamp"),
                SchemaFieldClass(fieldPath="raw_xml", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARIANT", description="Parsed XML VARIANT payload"),
            ],
        ),
        "o3_quarantine": (
            f"OPS.{mapping.targets.quarantine_table}",
            "O3 Quarantine Table: Holds XML files/records rejected by G1, G2, or G3 quality gates.",
            [
                SchemaFieldClass(fieldPath="file_name", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(512)", description="Quarantined file"),
                SchemaFieldClass(fieldPath="gate_id", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(8)", description="Quality gate (G1/G2/G3)"),
                SchemaFieldClass(fieldPath="failure_reason", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(2048)", description="Rejection reason"),
            ],
        ),
    }

    model = build_entity_model(mapping)
    for ent in model.entities:
        stg_key = f"staging_{ent.name}"
        stg_fields = [
            SchemaFieldClass(
                fieldPath=ent.pk_column,
                type=SchemaFieldDataTypeClass(type=StringTypeClass()),
                nativeDataType="VARCHAR(32)",
                description=f"Primary key for {ent.name}",
            )
        ]
        if ent.fk_column:
            stg_fields.append(
                SchemaFieldClass(
                    fieldPath=ent.fk_column,
                    type=SchemaFieldDataTypeClass(type=StringTypeClass()),
                    nativeDataType="VARCHAR(32)",
                    description=f"Foreign key referencing {ent.parent.name}.{ent.parent.pk_column}",
                )
            )
        stg_fields.extend([
            SchemaFieldClass(
                fieldPath=c.name,
                type=_sf_to_dh_type(c.field.snowflake_type),
                nativeDataType=c.field.snowflake_type,
                description=f"Extracted from XPath {c.field.xpath} (confidence={c.field.confidence})",
            )
            for c in ent.columns
        ])
        entity_descriptions[stg_key] = (
            f"STAGING.{ent.stage_table}",
            f"Layer 2 (Stage Dynamic Table): Entity {ent.name} ({ent.path}) extracted into typed columns.",
            stg_fields,
        )

        cur_key = f"curated_{ent.name}"
        cur_fields = [
            SchemaFieldClass(
                fieldPath=ent.pk_column,
                type=SchemaFieldDataTypeClass(type=StringTypeClass()),
                nativeDataType="VARCHAR(32)",
                description=f"Primary key for {ent.name}",
            )
        ]
        if ent.fk_column:
            cur_fields.append(
                SchemaFieldClass(
                    fieldPath=ent.fk_column,
                    type=SchemaFieldDataTypeClass(type=StringTypeClass()),
                    nativeDataType="VARCHAR(32)",
                    description=f"Foreign key referencing {ent.parent.name}.{ent.parent.pk_column}",
                )
            )
        cur_fields.extend([
            SchemaFieldClass(
                fieldPath=c.name,
                type=_sf_to_dh_type(c.field.snowflake_type),
                nativeDataType=c.field.snowflake_type,
                description=f"Gold business attribute from {c.field.xpath}",
            )
            for c in ent.columns
        ])
        cur_fields.append(
            SchemaFieldClass(fieldPath="_row_hash", type=SchemaFieldDataTypeClass(type=StringTypeClass()), nativeDataType="VARCHAR(64)", description="SHA-256 non-key attribute hash")
        )
        if ent.parent is None:
            cur_fields.extend([
                SchemaFieldClass(fieldPath="valid_start_time", type=SchemaFieldDataTypeClass(type=TimeTypeClass()), nativeDataType="TIMESTAMP_NTZ", description="Effective start timestamp"),
                SchemaFieldClass(fieldPath="valid_end_time", type=SchemaFieldDataTypeClass(type=TimeTypeClass()), nativeDataType="TIMESTAMP_NTZ", description="Effective end timestamp"),
                SchemaFieldClass(fieldPath="is_current", type=SchemaFieldDataTypeClass(type=BooleanTypeClass()), nativeDataType="BOOLEAN", description="Current active version flag"),
            ])
        entity_descriptions[cur_key] = (
            f"CURATED.{ent.curated_table}",
            f"Layer 3 (Final Gold Dynamic Table): Curated {ent.name} entity.",
            cur_fields,
        )

    for key, urn in entities.items():
        title, desc, fields = entity_descriptions.get(key, (key, f"Dataset {key}", []))
        props = DatasetPropertiesClass(
            name=title,
            description=desc,
            customProperties={
                "dataset": dataset,
                "schema_version": mapping.version,
                "source_system": manifest.source_system,
                "adls_landing_path": manifest.adls_landing_path,
                "freshness_sla_hours": str(manifest.freshness_sla_hours),
            },
        )
        schema_meta = SchemaMetadataClass(
            schemaName=title,
            platform="urn:li:dataPlatform:snowflake" if key != "adls_landing" else "urn:li:dataPlatform:adls",
            version=0,
            hash="",
            platformSchema=OtherSchemaClass(rawSchema=""),
            fields=fields,
        )
        for aspect in (props, ownership, tags, schema_meta):
            emitter.emit_mcp(MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect))
        emitted_urns.append(urn)

    # 2. Emit Upstream Lineage edges (ADLS -> RAW -> STAGE (each entity) -> CURATED (each entity))
    lineage_pairs: list[tuple[str, str]] = [
        (entities["adls_landing"], entities["d2_raw"]),
    ]
    for ent in model.entities:
        stg_urn = entities[f"staging_{ent.name}"]
        cur_urn = entities[f"curated_{ent.name}"]
        # Each stage table is fed from RAW
        lineage_pairs.append((entities["d2_raw"], stg_urn))
        # Curated table is fed from its corresponding stage table
        lineage_pairs.append((stg_urn, cur_urn))
    for up_urn, down_urn in lineage_pairs:
        up_lineage = UpstreamLineageClass(
            upstreams=[
                UpstreamClass(
                    dataset=up_urn,
                    type=DatasetLineageTypeClass.TRANSFORMED,
                    auditStamp=audit_stamp,
                )
            ]
        )
        emitter.emit_mcp(MetadataChangeProposalWrapper(entityUrn=down_urn, aspect=up_lineage))

    return {
        "live_emitted": True,
        "gms_server": gms_server,
        "emitted_urns_count": len(emitted_urns),
        "emitted_at": datetime.now(timezone.utc).isoformat(),
    }


def run_a2_catalog(dataset: str, registry_root: Path, env: str = "PROD") -> dict[str, Any]:
    """Emit DataHub entities, lineage graph, contracts, and ownership metadata."""
    ds_registry = registry_root / dataset
    manifest = OnboardingManifest.model_validate(
        yaml.safe_load((ds_registry / "onboarding_manifest.yaml").read_text(encoding="utf-8"))
    )
    mapping = DatasetMapping.model_validate(
        yaml.safe_load((ds_registry / "mapping.yaml").read_text(encoding="utf-8"))
    )

    dh_cfg = _load_datahub_settings()
    env = dh_cfg.get("env", env)
    gms_server = dh_cfg.get("gms_server", "http://localhost:8080")
    ui_url = dh_cfg.get("ui_url", "http://localhost:9002")

    def make_urn(table_name: str) -> str:
        return f"urn:li:dataset:(urn:li:dataPlatform:snowflake,{table_name},{env})"

    adls_urn = f"urn:li:dataset:(urn:li:dataPlatform:adls,{manifest.adls_landing_path.strip('/')},{env})"
    raw_urn = make_urn(f"RAW.{mapping.targets.raw_table}")
    quar_urn = make_urn(f"OPS.{mapping.targets.quarantine_table}")

    model = build_entity_model(mapping)
    entities = {
        "adls_landing": adls_urn,
        "d2_raw": raw_urn,
        "o3_quarantine": quar_urn,
    }

    upstream_lineage: list[dict[str, str]] = [
        {"upstream": adls_urn, "downstream": raw_urn, "mechanism": f"Snowpipe (RAW.pipe_{dataset}) -> Normal Table"},
    ]
    column_lineage: list[dict[str, Any]] = []

    for ent in model.entities:
        stg_urn = make_urn(f"STAGING.{ent.stage_table}")
        cur_urn = make_urn(f"CURATED.{ent.curated_table}")
        entities[f"staging_{ent.name}"] = stg_urn
        entities[f"curated_{ent.name}"] = cur_urn

        upstream_lineage.append({
            "upstream": raw_urn,
            "downstream": stg_urn,
            "mechanism": f"Dynamic Table (STAGING.{ent.stage_table})",
        })
        upstream_lineage.append({
            "upstream": stg_urn,
            "downstream": cur_urn,
            "mechanism": f"Dynamic Table (CURATED.{ent.curated_table})",
        })

        for c in ent.columns:
            column_lineage.append({
                "xpath": c.field.xpath,
                "entity": ent.name,
                "staging_column": f"{stg_urn}#{c.name}",
                "curated_column": f"{cur_urn}#{c.name}",
                "snowflake_type": c.field.snowflake_type,
            })

    # Backward-compatibility aliases for primary entity (d3_staging / d4_curated)
    entities["d3_staging"] = entities[f"staging_{model.primary.name}"]
    entities["d4_curated"] = entities[f"curated_{model.primary.name}"]

    live_status: dict[str, Any] = {"live_emitted": False, "gms_server": gms_server, "ui_url": ui_url}
    if dh_cfg.get("mode", "rest") == "rest":
        try:
            live_status = _emit_to_live_datahub(
                gms_server=gms_server,
                dataset=dataset,
                manifest=manifest,
                mapping=mapping,
                entities=entities,
            )
            live_status["ui_url"] = ui_url
        except Exception as exc:
            logger.warning("DataHub live GMS emission skipped (%s): %s", gms_server, exc)
            live_status = {
                "live_emitted": False,
                "gms_server": gms_server,
                "ui_url": ui_url,
                "note": f"Local file emitted (GMS unreachable: {exc})",
            }

    catalog_payload = {
        "dataset": dataset,
        "status": "PROVISIONED",
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "datahub_live": live_status,
        "owners": {
            "data_steward": manifest.data_steward,
            "data_engineering": manifest.engineering_owner,
            "platform_oncall": manifest.platform_oncall,
        },
        "sla_tags": {
            "freshness_sla_hours": manifest.freshness_sla_hours,
            "cdc_mode": "SCD_TYPE_2",
        },
        "entities": entities,
        "upstream_lineage": upstream_lineage,
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
