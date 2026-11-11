"""Step 2 — DDL Generator Agent.

Triggered ONLY after Human Approval (C3) on the Data Model & 3-Layer YAML schemas.
Responsibilities:
1. Reads approved `raw_schema.yaml`, `staging_schema.yaml`, `gold_schema.yaml`, `data_model.yaml`, and `mapping.yaml`.
2. Generates SQL scripts for all 3 layers and pipeline deployment artifacts:
   - `sql/01_raw_snowpipe.sql` (ADLS -> RAW via Snowpipe + Normal Table)
   - `sql/02_staging_dynamic_table.sql` (RAW -> Stage via Snowflake Dynamic Table)
   - `sql/03_gold_dynamic_table.sql` (Stage -> Final Gold via Snowflake Dynamic Table)
   - `sql/04_ops_quarantine_dq.sql` (Operational Quarantine & DQ tables)
   - `ddl.sql` (Consolidated master DDL script)
   - `pipeline_deployment_manifest.yaml` (Deployment artifact manifest for Step 3 Deployment Agent)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.ddl_compiler import (
    compile_gold_dynamic_table_sql,
    compile_ops_tables_sql,
    compile_raw_snowpipe_sql,
    compile_snowflake_ddl,
    compile_staging_dynamic_table_sql,
)
from src.models import (
    DataModelSpec,
    DatasetMapping,
    LayerSchemaYaml,
    OnboardingManifest,
    PipelineDeploymentManifest,
)
from src.snowflake_client import load_snowflake_config


def run_ddl_generator_agent(
    dataset: str,
    registry_root: Path,
    adls_stage: str = "@RAW.ADLS_XML_STAGE",
) -> PipelineDeploymentManifest:
    """Step 2: Generate SQLs for all 3 layers + pipeline deployment artifacts from approved YAMLs."""
    ds_registry = registry_root / dataset
    mapping_path = ds_registry / "mapping.yaml"
    if not mapping_path.exists():
        raise FileNotFoundError(f"DDL Generator Agent failed: missing mapping.yaml in {ds_registry}")

    mapping = DatasetMapping.model_validate(
        yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    )
    sf_cfg = load_snowflake_config()
    schema_raw = sf_cfg.schema_raw or "RAW"
    schema_staging = sf_cfg.schema_staging or "STAGING"
    schema_curated = sf_cfg.schema_curated or "CURATED"
    schema_ops = sf_cfg.schema_ops or "OPS"

    # Read 3-layer YAML schemas if present to extract target_lag & warehouse settings
    stage_lag = "5 minutes"
    stage_wh = "COMPUTE_WH"
    gold_lag = "15 minutes"
    gold_wh = "COMPUTE_WH"

    stg_yaml_path = ds_registry / "staging_schema.yaml"
    if stg_yaml_path.exists():
        stg_schema = LayerSchemaYaml.model_validate(
            yaml.safe_load(stg_yaml_path.read_text(encoding="utf-8"))
        )
        if stg_schema.tables:
            stage_lag = stg_schema.tables[0].target_lag or stage_lag
            stage_wh = stg_schema.tables[0].warehouse or stage_wh
        stg_schema.ddl_generated = True
        stg_yaml_path.write_text(
            yaml.safe_dump(stg_schema.model_dump(), sort_keys=False),
            encoding="utf-8",
        )

    gold_yaml_path = ds_registry / "gold_schema.yaml"
    if gold_yaml_path.exists():
        gold_schema = LayerSchemaYaml.model_validate(
            yaml.safe_load(gold_yaml_path.read_text(encoding="utf-8"))
        )
        if gold_schema.tables:
            gold_lag = gold_schema.tables[0].target_lag or gold_lag
            gold_wh = gold_schema.tables[0].warehouse or gold_wh
        gold_schema.ddl_generated = True
        gold_yaml_path.write_text(
            yaml.safe_dump(gold_schema.model_dump(), sort_keys=False),
            encoding="utf-8",
        )

    raw_yaml_path = ds_registry / "raw_schema.yaml"
    if raw_yaml_path.exists():
        raw_schema = LayerSchemaYaml.model_validate(
            yaml.safe_load(raw_yaml_path.read_text(encoding="utf-8"))
        )
        raw_schema.ddl_generated = True
        raw_yaml_path.write_text(
            yaml.safe_dump(raw_schema.model_dump(), sort_keys=False),
            encoding="utf-8",
        )

    sql_dir = ds_registry / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)

    # 1. Layer 1 SQL: ADLS -> RAW Normal Table + Snowpipe (Schema: RAW)
    raw_sql = compile_raw_snowpipe_sql(
        mapping,
        adls_stage=adls_stage,
        schema_raw=schema_raw,
    )
    raw_sql_path = sql_dir / "01_raw_snowpipe.sql"
    raw_sql_path.write_text(raw_sql, encoding="utf-8")

    # 2. Layer 2 SQL: RAW -> Stage Dynamic Table (Schema: STAGING)
    stage_sql = compile_staging_dynamic_table_sql(
        mapping,
        target_lag=stage_lag,
        warehouse=stage_wh,
        schema_raw=schema_raw,
        schema_staging=schema_staging,
    )
    stage_sql_path = sql_dir / "02_staging_dynamic_table.sql"
    stage_sql_path.write_text(stage_sql, encoding="utf-8")

    # 3. Layer 3 SQL: Stage -> Final Gold Dynamic Table (Schema: CURATED)
    gold_sql = compile_gold_dynamic_table_sql(
        mapping,
        target_lag=gold_lag,
        warehouse=gold_wh,
        schema_staging=schema_staging,
        schema_curated=schema_curated,
    )
    gold_sql_path = sql_dir / "03_gold_dynamic_table.sql"
    gold_sql_path.write_text(gold_sql, encoding="utf-8")

    # 4. Operational SQL: O3 Quarantine & O1 DQ Results (Schema: OPS)
    ops_sql = compile_ops_tables_sql(mapping, schema_ops=schema_ops)
    ops_sql_path = sql_dir / "04_ops_quarantine_dq.sql"
    ops_sql_path.write_text(ops_sql, encoding="utf-8")

    # 5. Consolidated ddl.sql
    full_ddl = compile_snowflake_ddl(
        mapping,
        adls_stage=adls_stage,
        schema_raw=schema_raw,
        schema_staging=schema_staging,
        schema_curated=schema_curated,
        schema_ops=schema_ops,
    )
    (ds_registry / "ddl.sql").write_text(full_ddl, encoding="utf-8")

    # 6. Pipeline Deployment Manifest
    deployment_manifest = PipelineDeploymentManifest(
        dataset=dataset,
        version=mapping.version,
        generated_by="step2_ddl_generator_agent",
        adls_to_raw_mechanism="SNOWPIPE",
        raw_to_stage_mechanism="DYNAMIC_TABLE",
        stage_to_gold_mechanism="DYNAMIC_TABLE",
        sql_artifacts={
            "raw_layer_sql": str(raw_sql_path),
            "stage_layer_sql": str(stage_sql_path),
            "gold_layer_sql": str(gold_sql_path),
            "ops_tables_sql": str(ops_sql_path),
            "master_ddl_sql": str(ds_registry / "ddl.sql"),
        },
        execution_order=[
            "sql/01_raw_snowpipe.sql",
            "sql/02_staging_dynamic_table.sql",
            "sql/03_gold_dynamic_table.sql",
            "sql/04_ops_quarantine_dq.sql",
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    (ds_registry / "pipeline_deployment_manifest.yaml").write_text(
        yaml.safe_dump(deployment_manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    manifest_path = ds_registry / "onboarding_manifest.yaml"
    if manifest_path.exists():
        manifest = OnboardingManifest.model_validate(
            yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        )
        manifest.status = "DDL_GENERATED"
        manifest_path.write_text(
            yaml.safe_dump(manifest.model_dump(), sort_keys=False),
            encoding="utf-8",
        )

    return deployment_manifest

