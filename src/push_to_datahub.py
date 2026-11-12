"""Pushes the bootstrapped orders dataset, schema, owners, tags, and lineage to DataHub GMS via REST emitter."""
from __future__ import annotations

from pathlib import Path
import yaml

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    OwnerClass,
    OwnershipClass,
    OwnershipTypeClass,
    GlobalTagsClass,
    TagAssociationClass,
    UpstreamLineageClass,
    UpstreamClass,
    DatasetLineageTypeClass,
    SchemaMetadataClass,
    SchemaFieldDataTypeClass,
    SchemaFieldClass,
    StringTypeClass,
    NumberTypeClass,
    DateTypeClass,
    TimeTypeClass,
    BooleanTypeClass,
    NullTypeClass,
    OtherSchemaClass,
)

BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_DIR = BASE_DIR / "registry" / "orders"

def map_type_to_datahub(sf_type: str):
    t = sf_type.upper()
    if "NUMBER" in t or "INT" in t or "FLOAT" in t or "DECIMAL" in t:
        return SchemaFieldDataTypeClass(type=NumberTypeClass())
    elif "DATE" in t:
        return SchemaFieldDataTypeClass(type=DateTypeClass())
    elif "TIMESTAMP" in t or "TIME" in t:
        return SchemaFieldDataTypeClass(type=TimeTypeClass())
    elif "BOOLEAN" in t:
        return SchemaFieldDataTypeClass(type=BooleanTypeClass())
    elif "VARCHAR" in t or "TEXT" in t or "STRING" in t:
        return SchemaFieldDataTypeClass(type=StringTypeClass())
    return SchemaFieldDataTypeClass(type=NullTypeClass())

def push_orders_to_datahub():
    gms_server = "http://localhost:8080"
    emitter = DatahubRestEmitter(gms_server=gms_server)
    
    mapping_data = yaml.safe_load((REGISTRY_DIR / "mapping.yaml").read_text(encoding="utf-8"))
    manifest_data = yaml.safe_load((REGISTRY_DIR / "onboarding_manifest.yaml").read_text(encoding="utf-8"))
    
    env = "PROD"
    platform_sf = "snowflake"
    platform_adls = "adls"
    
    # URNs
    adls_urn = f"urn:li:dataset:(urn:li:dataPlatform:{platform_adls},landing/xml/orders,{env})"
    raw_urn = f"urn:li:dataset:(urn:li:dataPlatform:{platform_sf},raw_orders,{env})"
    stg_urn = f"urn:li:dataset:(urn:li:dataPlatform:{platform_sf},staging_orders,{env})"
    cur_urn = f"urn:li:dataset:(urn:li:dataPlatform:{platform_sf},curated_orders,{env})"
    
    print(f"Connecting to DataHub GMS at {gms_server}...")
    
    # 1. Register ADLS Landing Dataset
    emitter.emit_mcp(
        MetadataChangeProposalWrapper(
            entityUrn=adls_urn,
            aspect=DatasetPropertiesClass(
                name="ADLS Raw XML Orders Landing",
                description="Landing zone for raw order XML files from source ERP system",
                customProperties={"landing_path": manifest_data.get("adls_landing_path", "")}
            )
        )
    )
    
    # 2. Register Raw, Staging, and Curated Tables with Ownership & Tags
    owners = [
        OwnerClass(owner=f"urn:li:corpuser:{manifest_data['data_steward'].split('@')[0]}", type=OwnershipTypeClass.DATA_STEWARD),
        OwnerClass(owner=f"urn:li:corpuser:{manifest_data['engineering_owner'].split('@')[0]}", type=OwnershipTypeClass.DATAOWNER),
    ]
    
    tags = GlobalTagsClass(
        tags=[
            TagAssociationClass(tag="urn:li:tag:XML_Pipeline"),
            TagAssociationClass(tag=f"urn:li:tag:SLA_{manifest_data.get('freshness_sla_hours', 24)}h"),
            TagAssociationClass(tag="urn:li:tag:SCD_Type_2"),
        ]
    )
    
    # Build Schema Metadata for Curated Table
    schema_fields = []
    for f in mapping_data["fields"]:
        schema_fields.append(
            SchemaFieldClass(
                fieldPath=f["column"],
                type=map_type_to_datahub(f["snowflake_type"]),
                nativeDataType=f["snowflake_type"],
                description=f"Inferred from XML XPath: {f['xpath']} (Confidence: {f['confidence'] * 100:.0f}%, Required: {f['required']})"
            )
        )
    
    # Add SCD2 audit columns
    for col, ctype in [
        ("valid_start_time", "TIMESTAMP_NTZ"),
        ("valid_end_time", "TIMESTAMP_NTZ"),
        ("is_current", "BOOLEAN"),
        ("_row_hash", "VARCHAR(64)"),
        ("_source_file", "VARCHAR(512)")
    ]:
        schema_fields.append(
            SchemaFieldClass(
                fieldPath=col,
                type=map_type_to_datahub(ctype),
                nativeDataType=ctype,
                description="SCD Type 2 CDC audit tracking column"
            )
        )
        
    curated_schema = SchemaMetadataClass(
        schemaName="curated_orders_schema",
        platform=f"urn:li:dataPlatform:{platform_sf}",
        version=int(mapping_data["version"].split(".")[1]),
        hash="",
        platformSchema=OtherSchemaClass(rawSchema="Snowflake DDL (SCD Type 2)"),
        fields=schema_fields
    )

    # Emit Raw & Staging properties
    emitter.emit_mcp(MetadataChangeProposalWrapper(
        entityUrn=raw_urn,
        aspect=DatasetPropertiesClass(
            name="raw_orders",
            description="Immutable Snowflake Raw Layer storing XML in VARIANT with ingestion metadata."
        )
    ))
    emitter.emit_mcp(MetadataChangeProposalWrapper(
        entityUrn=stg_urn,
        aspect=DatasetPropertiesClass(
            name="staging_orders",
            description="Flattened, typed staging layer extracted using LATERAL FLATTEN."
        )
    ))

    # Emit Curated Dataset
    emitter.emit_mcp(MetadataChangeProposalWrapper(
        entityUrn=cur_urn,
        aspect=DatasetPropertiesClass(
            name="curated_orders",
            description="Published, curated orders dataset with SCD Type 2 history for analytics."
        )
    ))
    emitter.emit_mcp(MetadataChangeProposalWrapper(entityUrn=cur_urn, aspect=OwnershipClass(owners=owners)))
    emitter.emit_mcp(MetadataChangeProposalWrapper(entityUrn=cur_urn, aspect=tags))
    emitter.emit_mcp(MetadataChangeProposalWrapper(entityUrn=cur_urn, aspect=curated_schema))
    
    # 3. Emit Lineage: ADLS -> raw_orders -> staging_orders -> curated_orders
    emitter.emit_mcp(MetadataChangeProposalWrapper(
        entityUrn=raw_urn,
        aspect=UpstreamLineageClass(
            upstreams=[UpstreamClass(dataset=adls_urn, type=DatasetLineageTypeClass.TRANSFORMED)]
        )
    ))
    emitter.emit_mcp(MetadataChangeProposalWrapper(
        entityUrn=stg_urn,
        aspect=UpstreamLineageClass(
            upstreams=[UpstreamClass(dataset=raw_urn, type=DatasetLineageTypeClass.TRANSFORMED)]
        )
    ))
    emitter.emit_mcp(MetadataChangeProposalWrapper(
        entityUrn=cur_urn,
        aspect=UpstreamLineageClass(
            upstreams=[UpstreamClass(dataset=stg_urn, type=DatasetLineageTypeClass.TRANSFORMED)]
        )
    ))

    print("Successfully pushed dataset, schema, ownership, tags, and lineage to DataHub!")
    print(f"Direct link to view in DataHub: http://localhost:9002/dataset/{cur_urn}")

if __name__ == "__main__":
    push_orders_to_datahub()
