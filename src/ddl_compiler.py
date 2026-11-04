"""Compiles a DatasetMapping (mapping.yaml) into Snowflake DDL, Snowpipe, Streams, Tasks, and SCD2 MERGE SQL."""
from __future__ import annotations

from src.models import DatasetMapping, FieldMapping


def compile_snowflake_ddl(mapping: DatasetMapping, adls_stage: str = "@RAW.ADLS_XML_STAGE") -> str:
    """Generate complete idempotent Snowflake DDL for D2, D3, D4 (SCD2), O1, and O3."""
    ds = mapping.dataset
    raw_tbl = mapping.targets.raw_table
    stg_tbl = mapping.targets.staging_table
    cur_tbl = mapping.targets.curated_table
    quar_tbl = mapping.targets.quarantine_table
    dq_tbl = mapping.targets.dq_results_table

    col_defs = []
    select_exprs = []
    for f in mapping.fields:
        null_clause = "NOT NULL" if (f.required and f.column in mapping.business_keys) else "NULL"
        col_defs.append(f"    {f.column:<30} {f.snowflake_type:<16} {null_clause}")
        select_exprs.append(f"    {f.xml_expr} AS {f.column}")

    cols_sql = ",\n".join(col_defs)
    select_sql = ",\n".join(select_exprs)

    # Build LATERAL FLATTEN clause if any array field exists
    array_fields = [f for f in mapping.fields if f.is_array and f.flatten_path]
    if array_fields:
        fp = array_fields[0].flatten_path or ""
        fp_parts = [p for p in fp.strip("/").split("/") if p]
        root_prefix = mapping.root_element.strip("/")
        rel_parts = fp_parts[1:] if (fp_parts and fp_parts[0] == root_prefix) else fp_parts
        parent_Parts = rel_parts[:-1]
        expr = "r.raw_xml"
        for p in parent_Parts:
            expr = f"XMLGET({expr}, '{p}')"
        flatten_clause = f",\n    LATERAL FLATTEN(INPUT => {expr}:'$') item\nWHERE GET(item.value, '@') = '{rel_parts[-1]}'"
    else:
        flatten_clause = ""

    # SCD Type 2 join & hash expressions
    bk_join = " AND ".join(f"tgt.{k} = src.{k}" for k in mapping.business_keys)
    non_key_cols = [f.column for f in mapping.fields if f.column not in mapping.business_keys]
    hash_cols = ", ".join(f"COALESCE(TO_VARCHAR({c}), '')" for c in non_key_cols) or "'1'"
    all_field_cols = ", ".join(f.column for f in mapping.fields)
    src_field_cols = ", ".join(f"src.{f.column}" for f in mapping.fields)

    return f"""-- =============================================================================
-- AUTO-GENERATED SNOWFLAKE DDL FROM C4 REGISTRY: {ds} (version {mapping.version})
-- Source: {mapping.source} | Root XML Element: {mapping.root_element}
-- =============================================================================

-- 1. D2: IMMUTABLE RAW LAYER (VARIANT + FILE METADATA)
CREATE TABLE IF NOT EXISTS {raw_tbl} (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _source_system      VARCHAR(128)    NOT NULL,
    _load_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_{raw_tbl}_file_hash UNIQUE (_file_name, _file_sha256)
);

-- Snowpipe (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS pipe_{ds}
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for {ds} XML ingestion from ADLS'
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

ALTER PIPE IF EXISTS pipe_{ds} SET PIPE_EXECUTION_PAUSED = TRUE;

-- Stream on Raw Table for incremental D2 -> D3 processing
CREATE STREAM IF NOT EXISTS stream_{raw_tbl}
    ON TABLE {raw_tbl}
    APPEND_ONLY = TRUE;

-- 2. D3: TYPED STAGING TABLE (LATERAL FLATTEN)
CREATE TABLE IF NOT EXISTS {stg_tbl} (
{cols_sql},
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _staged_ts          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);

-- Task to flatten XML from Stream into Typed Staging
CREATE OR REPLACE TASK task_flatten_{ds}
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('stream_{raw_tbl}')
AS
INSERT INTO {stg_tbl} (
    {all_field_cols},
    _file_name,
    _file_sha256
)
SELECT
{select_sql},
    r._file_name,
    r._file_sha256
FROM stream_{raw_tbl} r{flatten_clause};

-- 3. D4: CURATED DATASET WITH CDC SCD TYPE 2
CREATE TABLE IF NOT EXISTS {cur_tbl} (
{cols_sql},
    _row_hash           VARCHAR(64)     NOT NULL,
    is_valid_start      TIMESTAMP_NTZ   NOT NULL,
    is_valid_end        TIMESTAMP_NTZ   NULL,
    is_current          BOOLEAN         NOT NULL DEFAULT TRUE,
    system_start_time   TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    system_end_time     TIMESTAMP_NTZ   NULL,
    _source_file        VARCHAR(512)    NOT NULL
);

-- Task to apply SCD Type 2 (close changed current rows, insert new version)
CREATE OR REPLACE TASK task_scd2_{ds}
    WAREHOUSE = COMPUTE_WH
    AFTER task_flatten_{ds}
AS
BEGIN
    -- Step A: Close existing current rows where non-key attributes changed
    UPDATE {cur_tbl} tgt
    SET
        tgt.is_valid_end = CURRENT_TIMESTAMP(),
        tgt.is_current = FALSE,
        tgt.system_end_time = CURRENT_TIMESTAMP()
    FROM (
        SELECT
            {all_field_cols},
            SHA2(CONCAT_WS('|', {hash_cols}), 256) AS _row_hash
        FROM {stg_tbl}
    ) src
    WHERE {bk_join}
      AND tgt.is_current = TRUE
      AND tgt._row_hash <> src._row_hash;

    -- Step B: Insert brand-new keys or newly versioned rows
    INSERT INTO {cur_tbl} (
        {all_field_cols},
        _row_hash,
        is_valid_start,
        is_valid_end,
        is_current,
        system_start_time,
        system_end_time,
        _source_file
    )
    SELECT
        {src_field_cols},
        src._row_hash,
        CURRENT_TIMESTAMP(),
        NULL,
        TRUE,
        CURRENT_TIMESTAMP(),
        NULL,
        src._file_name
    FROM (
        SELECT
            {all_field_cols},
            _file_name,
            SHA2(CONCAT_WS('|', {hash_cols}), 256) AS _row_hash
        FROM {stg_tbl}
    ) src
    LEFT JOIN {cur_tbl} tgt
      ON {bk_join} AND tgt.is_current = TRUE
    WHERE tgt.{mapping.business_keys[0]} IS NULL;
END;

-- 4. O3: QUARANTINE TABLE & O1: DQ RESULTS TABLE
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


def compile_additive_drift_sql(dataset: str, new_fields: list[FieldMapping]) -> list[str]:
    """Generate ALTER TABLE ADD COLUMN statements for auto-applied additive schema drift."""
    statements: list[str] = []
    for f in new_fields:
        statements.append(
            f"ALTER TABLE staging_{dataset} ADD COLUMN IF NOT EXISTS {f.column} {f.snowflake_type} NULL;"
        )
        statements.append(
            f"ALTER TABLE curated_{dataset} ADD COLUMN IF NOT EXISTS {f.column} {f.snowflake_type} NULL;"
        )
    return statements
