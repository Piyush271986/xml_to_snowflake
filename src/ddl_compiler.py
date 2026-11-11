"""Compiles 3-layer YAML schemas & DatasetMapping into Snowflake DDL (Snowpipe + Dynamic Tables)."""
from __future__ import annotations

from src.entity_model import Entity, EntityColumn, build_entity_model
from src.models import DatasetMapping, FieldMapping
from src.xml_infer import cast_varchar_expr


def _xmlget_chain(base: str, parts: list[str]) -> str:
    expr = base
    for p in parts:
        expr = f"XMLGET({expr}, '{p}')"
    return expr


def _flatten_plan(entity: Entity, root_path: str) -> tuple[list[str], list[str]]:
    """LATERAL FLATTEN joins (aliases a1..ak) and WHERE predicates reaching `entity` from `r.raw_xml`."""
    joins: list[str] = []
    wheres: list[str] = []
    base = "r.raw_xml"
    parent_parts = [p for p in root_path.strip("/").split("/") if p]
    level = 0
    for ent in entity.chain():
        if not ent.is_flattened:
            continue
        level += 1
        parts = [p for p in ent.path.strip("/").split("/") if p]
        container = _xmlget_chain(base, parts[len(parent_parts) : -1])
        content = f"GET({container}, '$')"
        joins.append(
            f"LATERAL FLATTEN(INPUT => IFF(IS_ARRAY({content}), {content}, ARRAY_CONSTRUCT({content}))) a{level}"
        )
        wheres.append(f"GET(a{level}.value, '@')::VARCHAR = '{parts[-1]}'")
        base = f"a{level}.value"
        parent_parts = parts
    return joins, wheres


def _levels(entity: Entity) -> int:
    return sum(1 for e in entity.chain() if e.is_flattened)


def _pk_expr(levels: int) -> str:
    """Deterministic surrogate key: file identity plus the element position at every repeating level."""
    idx = "".join(f", a{i}.index::VARCHAR" for i in range(1, levels + 1))
    return f"MD5(CONCAT_WS('|', r._file_name, r._file_sha256{idx}))"


def _column_expr(entity: Entity, col: EntityColumn) -> str:
    if col.from_document or not entity.is_flattened:
        base = "r.raw_xml"
    else:
        base = f"a{_levels(entity)}.value"
    node = _xmlget_chain(base, col.element_parts)
    raw = f'{node}:"@{col.attribute}"::VARCHAR' if col.attribute else f'{node}:"$"::VARCHAR'
    return cast_varchar_expr(raw, col.field.snowflake_type)


def _fk_comment(entity: Entity, layer_table: str, parent_table: str | None) -> str:
    if entity.parent is None or parent_table is None:
        return f"{layer_table}: root entity {entity.name} (PK {entity.pk_column})"
    return f"{layer_table}: child of {parent_table} via {entity.fk_column} -> {parent_table}.{entity.parent.pk_column} (logical FK)"

def compile_raw_snowpipe_sql(
    mapping: DatasetMapping,
    adls_stage: str = "@RAW.ADLS_XML_STAGE",
    schema_raw: str = "RAW",
) -> str:
    """Layer 1 DDL: ADLS -> RAW Normal Table + Snowpipe (deployed under RAW schema)."""
    ds = mapping.dataset
    raw_tbl = f"{schema_raw}.{mapping.targets.raw_table}" if schema_raw else mapping.targets.raw_table
    pipe_fqn = f"{schema_raw}.pipe_{ds}" if schema_raw else f"pipe_{ds}"
    return f"""-- =============================================================================
-- LAYER 1 (RAW): NORMAL TABLE + ADLS SNOWPIPE ({ds} v{mapping.version}) [Schema: {schema_raw}]
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS {schema_raw};

CREATE TABLE IF NOT EXISTS {raw_tbl} (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _source_system      VARCHAR(128)    NOT NULL,
    _load_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_{mapping.targets.raw_table}_file_hash UNIQUE (_file_name, _file_sha256)
);

-- Snowpipe: ADLS to RAW Normal Table (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS {pipe_fqn}
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for {ds} XML ingestion from ADLS into {raw_tbl}'
AS
COPY INTO {raw_tbl} (_file_name, _file_sha256, _source_system, raw_xml)
FROM (
    SELECT
        METADATA$FILENAME,
        METADATA$FILE_CONTENT_KEY,
        '{ds}',
        $1
    FROM {adls_stage}/{ds}/
)
FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = FALSE);

ALTER PIPE IF EXISTS {pipe_fqn} SET PIPE_EXECUTION_PAUSED = TRUE;
"""


def compile_staging_dynamic_table_sql(
    mapping: DatasetMapping,
    target_lag: str = "5 minutes",
    warehouse: str = "COMPUTE_WH",
    schema_raw: str = "RAW",
    schema_staging: str = "STAGING",
) -> str:
    """Layer 2 DDL: RAW -> one Stage Dynamic Table per XML entity (parent + each child), under the STAGING schema."""
    ds = mapping.dataset
    model = build_entity_model(mapping)
    raw_tbl = f"{schema_raw}.{mapping.targets.raw_table}" if schema_raw else mapping.targets.raw_table
    prefix = f"{schema_staging}." if schema_staging else ""

    blocks: list[str] = [
        f"""-- =============================================================================
-- LAYER 2 (STAGE): ONE DYNAMIC TABLE PER XML ENTITY FROM RAW ({ds} v{mapping.version}) [Schema: {schema_staging}]
-- Entities: {', '.join(e.name for e in model.entities)}
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS {schema_staging};
"""
    ]
    for ent in model.entities:
        stg_tbl = f"{prefix}{ent.stage_table}"
        parent_tbl = f"{prefix}{ent.parent.stage_table}" if ent.parent else None
        joins, wheres = _flatten_plan(ent, model.root_path)
        levels = _levels(ent)

        select_exprs = [f"    {_pk_expr(levels)} AS {ent.pk_column}"]
        if ent.parent is not None:
            select_exprs.append(f"    {_pk_expr(levels - 1)} AS {ent.fk_column}")
        select_exprs.extend(f"    {_column_expr(ent, c)} AS {c.name}" for c in ent.columns)
        select_exprs.extend(
            [
                "    r._file_name AS _file_name",
                "    r._file_sha256 AS _file_sha256",
                "    r._load_ts AS _staged_ts",
            ]
        )
        from_sql = f"FROM {raw_tbl} r"
        if joins:
            from_sql += ",\n    " + ",\n    ".join(joins)
        where_sql = ("\nWHERE " + "\n  AND ".join(wheres)) if wheres else ""
        blocks.append(
            f"""-- Entity `{ent.name}` ({ent.path})
CREATE OR REPLACE DYNAMIC TABLE {stg_tbl}
    TARGET_LAG = '{target_lag}'
    WAREHOUSE = {warehouse}
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = '{_fk_comment(ent, stg_tbl, parent_tbl)}'
AS
SELECT
{",\n".join(select_exprs)}
{from_sql}{where_sql};
"""
        )
    return "\n".join(blocks)


def compile_gold_dynamic_table_sql(
    mapping: DatasetMapping,
    target_lag: str = "15 minutes",
    warehouse: str = "COMPUTE_WH",
    schema_staging: str = "STAGING",
    schema_curated: str = "CURATED",
) -> str:
    """Layer 3 DDL: Stage -> one curated Dynamic Table per XML entity (parent versioned SCD2, children keyed by FK)."""
    ds = mapping.dataset
    model = build_entity_model(mapping)
    stg_prefix = f"{schema_staging}." if schema_staging else ""
    cur_prefix = f"{schema_curated}." if schema_curated else ""

    blocks: list[str] = [
        f"""-- =============================================================================
-- LAYER 3 (CURATED): ONE DYNAMIC TABLE PER XML ENTITY FROM STAGE ({ds} v{mapping.version}) [Schema: {schema_curated}]
-- Entities: {', '.join(e.name for e in model.entities)}
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS {schema_curated};
"""
    ]
    for ent in model.entities:
        stg_tbl = f"{stg_prefix}{ent.stage_table}"
        cur_tbl = f"{cur_prefix}{ent.curated_table}"
        parent_tbl = f"{cur_prefix}{ent.parent.curated_table}" if ent.parent else None
        key_cols = [ent.pk_column] + ([ent.fk_column] if ent.fk_column else [])
        data_cols = [c.name for c in ent.columns]
        non_key = [c for c in data_cols if c not in ent.business_keys]
        hash_cols = ", ".join(f"COALESCE(TO_VARCHAR({c}), '')" for c in non_key) or "'1'"
        select_cols = ",\n        ".join(key_cols + data_cols)

        if ent.parent is None:
            partition = ", ".join(ent.business_keys) if ent.business_keys else ent.pk_column
            body = f"""WITH versioned AS (
    SELECT
        {select_cols},
        SHA2(CONCAT_WS('|', {hash_cols}), 256) AS _row_hash,
        _staged_ts AS is_valid_start,
        LEAD(_staged_ts) OVER (
            PARTITION BY {partition}
            ORDER BY _staged_ts ASC
        ) AS is_valid_end,
        CASE
            WHEN LEAD(_staged_ts) OVER (
                PARTITION BY {partition}
                ORDER BY _staged_ts ASC
            ) IS NULL THEN TRUE
            ELSE FALSE
        END AS is_current,
        _staged_ts AS system_start_time,
        LEAD(_staged_ts) OVER (
            PARTITION BY {partition}
            ORDER BY _staged_ts ASC
        ) AS system_end_time,
        _file_name AS _source_file
    FROM {stg_tbl}
)
SELECT * FROM versioned"""
        else:
            body = f"""SELECT
        {select_cols},
        SHA2(CONCAT_WS('|', {hash_cols}), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM {stg_tbl}"""
        blocks.append(
            f"""-- Entity `{ent.name}` ({ent.path})
CREATE OR REPLACE DYNAMIC TABLE {cur_tbl}
    TARGET_LAG = '{target_lag}'
    WAREHOUSE = {warehouse}
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = '{_fk_comment(ent, cur_tbl, parent_tbl)}'
AS
{body};
"""
        )
    return "\n".join(blocks)

def compile_ops_tables_sql(
    mapping: DatasetMapping,
    schema_ops: str = "OPS",
) -> str:
    """Operational tables: O3 Quarantine & O1 DQ Results (deployed under OPS schema)."""
    quar_tbl = f"{schema_ops}.{mapping.targets.quarantine_table}" if schema_ops else mapping.targets.quarantine_table
    dq_tbl = f"{schema_ops}.{mapping.targets.dq_results_table}" if schema_ops else mapping.targets.dq_results_table
    return f"""-- =============================================================================
-- OPERATIONAL TABLES: O3 QUARANTINE & O1 DQ RESULTS [Schema: {schema_ops}]
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS {schema_ops};

CREATE TABLE IF NOT EXISTS {quar_tbl} (
    quarantine_id       VARCHAR(64)     DEFAULT UUID_STRING(),
    dataset             VARCHAR(128)    NOT NULL,
    file_name           VARCHAR(512)    NOT NULL,
    file_sha256         VARCHAR(64)     NOT NULL,
    gate_id             VARCHAR(8)      NOT NULL, -- G1, G2, G3
    failure_reason      VARCHAR(2048)   NOT NULL,
    raw_payload         VARIANT         NULL,
    quarantined_at      TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    replayed            BOOLEAN         DEFAULT FALSE,
    replayed_at         TIMESTAMP_NTZ   NULL
);

CREATE TABLE IF NOT EXISTS {dq_tbl} (
    check_id            VARCHAR(64)     DEFAULT UUID_STRING(),
    dataset             VARCHAR(128)    NOT NULL,
    file_name           VARCHAR(512)    NOT NULL,
    gate_id             VARCHAR(8)      NOT NULL,
    check_name          VARCHAR(256)    NOT NULL,
    passed              BOOLEAN         NOT NULL,
    details             VARCHAR(2048)   NULL,
    checked_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);
"""


def compile_snowflake_ddl(
    mapping: DatasetMapping,
    adls_stage: str = "@RAW.ADLS_XML_STAGE",
    schema_raw: str = "RAW",
    schema_staging: str = "STAGING",
    schema_curated: str = "CURATED",
    schema_ops: str = "OPS",
) -> str:
    """Generate complete idempotent Snowflake DDL for RAW (Snowpipe), STAGE (Dynamic Table), GOLD (Dynamic Table), O1, and O3."""
    parts = [
        f"-- =============================================================================",
        f"-- AUTO-GENERATED SNOWFLAKE DDL BY STEP 2 DDL GENERATOR AGENT: {mapping.dataset} (v{mapping.version})",
        f"-- Architecture: ADLS -> Snowpipe ({schema_raw}) -> STAGE Dynamic Table ({schema_staging}) -> GOLD Dynamic Table ({schema_curated})",
        f"-- =============================================================================\n",
        compile_raw_snowpipe_sql(mapping, adls_stage=adls_stage, schema_raw=schema_raw),
        compile_staging_dynamic_table_sql(mapping, schema_raw=schema_raw, schema_staging=schema_staging),
        compile_gold_dynamic_table_sql(mapping, schema_staging=schema_staging, schema_curated=schema_curated),
        compile_ops_tables_sql(mapping, schema_ops=schema_ops),
    ]
    return "\n".join(parts)


def compile_additive_drift_sql(dataset: str, new_fields: list[FieldMapping]) -> list[str]:
    """Generate DDL statements for auto-applied additive schema drift on Stage and Gold Dynamic Tables."""
    statements: list[str] = []
    for f in new_fields:
        statements.append(
            f"-- Additive drift column for Dynamic Table staging_{dataset}: {f.column} ({f.snowflake_type})"
        )
        statements.append(
            f"ALTER DYNAMIC TABLE IF EXISTS staging_{dataset} REFRESH;"
        )
        statements.append(
            f"ALTER DYNAMIC TABLE IF EXISTS curated_{dataset} REFRESH;"
        )
    return statements
