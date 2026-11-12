-- =============================================================================
-- AUTO-GENERATED SNOWFLAKE DDL BY STEP 2 DDL GENERATOR AGENT: analytics (v0.1.0)
-- Architecture: ADLS -> Snowpipe (RAW) -> STAGE Dynamic Table (STAGING) -> GOLD Dynamic Table (CURATED)
-- =============================================================================

-- =============================================================================
-- LAYER 1 (RAW): NORMAL TABLE + ADLS SNOWPIPE (analytics v0.1.0) [Schema: RAW]
-- Record XPath: /ASSETS/ASSET/BND_CORP (loaded record-by-record into separate VARIANT rows)
-- Preserved Top-Level Tags: /ASSETS/@ASOF_DATE, /ASSETS/@CREATE_DATE, /ASSETS/@RECORDS
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS RAW;

CREATE TABLE IF NOT EXISTS RAW.raw_analytics (
    _file_name          VARCHAR(512)    NOT NULL,
    _file_sha256        VARCHAR(64)     NOT NULL,
    _record_index       NUMBER(18,0)    NOT NULL DEFAULT 0,
    _source_system      VARCHAR(128)    NOT NULL,
    _ingestion_ts            TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP(),
    raw_xml             VARIANT         NOT NULL,
    CONSTRAINT uq_raw_analytics_file_hash UNIQUE (_file_name, _file_sha256, _record_index)
);

-- Snowpipe: ADLS to RAW Normal Table (Created PAUSED during onboarding; enabled at Stage 9 Go-Live)
CREATE PIPE IF NOT EXISTS RAW.pipe_analytics
    AUTO_INGEST = TRUE
    COMMENT = 'Snowpipe for analytics XML ingestion from ADLS into RAW.raw_analytics (record path: /ASSETS/ASSET/BND_CORP)'
AS
COPY INTO RAW.raw_analytics (_file_name, _file_sha256, _source_system, raw_xml)
FROM (
    SELECT
        METADATA$FILENAME,
        METADATA$FILE_CONTENT_KEY,
        'analytics',
        $1
    FROM @RAW.ADLS_XML_STAGE/analytics/
)
FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = TRUE);

ALTER PIPE IF EXISTS RAW.pipe_analytics SET PIPE_EXECUTION_PAUSED = TRUE;

-- =============================================================================
-- LAYER 2 (STAGE): ONE DYNAMIC TABLE PER XML ENTITY FROM RAW (analytics v0.1.0) [Schema: STAGING]
-- Record XPath in RAW: /ASSETS/ASSET/BND_CORP
-- Entities: asset, country_classification, cusip2, cusip_alias
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS STAGING;

-- Entity `asset` (/ASSETS/ASSET)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = INCREMENTAL
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics: root entity asset (PK asset_pk)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR)) AS asset_pk,
    r.raw_xml:"@ASOF_DATE"::VARCHAR AS asof_date,
    r.raw_xml:"@CREATE_DATE"::VARCHAR AS create_date,
    TRY_TO_NUMBER(r.raw_xml:"@RECORDS"::VARCHAR, 18, 0) AS records,
    XMLGET(r.raw_xml, 'CLASS'):"$"::VARCHAR AS class_val,
    XMLGET(r.raw_xml, 'ACCRUAL_DT'):"$"::VARCHAR AS accrual_dt,
    TRY_TO_NUMBER(XMLGET(r.raw_xml, 'AMT_ISU'):"$"::VARCHAR, 18, 0) AS amt_isu,
    XMLGET(r.raw_xml, 'ANNOUNCE_DT'):"$"::VARCHAR AS announce_dt,
    TRY_TO_NUMBER(XMLGET(r.raw_xml, 'CALC_TYPE'):"$"::VARCHAR, 18, 0) AS calc_type,
    XMLGET(r.raw_xml, 'CALL_MANDATORY'):"$"::VARCHAR AS call_mandatory,
    XMLGET(r.raw_xml, 'CALL_TYPE'):"$"::VARCHAR AS call_type,
    XMLGET(r.raw_xml, 'CD_INSTMT_TYPE'):"$"::VARCHAR AS cd_instmt_type,
    XMLGET(r.raw_xml, 'CHANGE_DT'):"$"::VARCHAR AS change_dt,
    TRY_TO_NUMBER(XMLGET(r.raw_xml, 'COMPOUND_FLAG'):"$"::VARCHAR, 18, 0) AS compound_flag,
    XMLGET(r.raw_xml, 'COUNTRY'):"$"::VARCHAR AS country,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'COUPON_FIX'):"$"::VARCHAR, 18, 4) AS coupon_fix,
    XMLGET(r.raw_xml, 'COUP_FREQ'):"$"::VARCHAR AS coup_freq,
    XMLGET(r.raw_xml, 'CPN_TYPE'):"$"::VARCHAR AS cpn_type,
    XMLGET(r.raw_xml, 'CURRENCY'):"$"::VARCHAR AS currency,
    XMLGET(r.raw_xml, 'CUSIP'):"$"::VARCHAR AS cusip,
    XMLGET(r.raw_xml, 'CUSIP_TYPE'):"$"::VARCHAR AS cusip_type,
    XMLGET(r.raw_xml, 'DATE_CONV'):"$"::VARCHAR AS date_conv,
    XMLGET(r.raw_xml, 'DESC_INSTMT'):"$"::VARCHAR AS desc_instmt,
    XMLGET(r.raw_xml, 'END_ADJ_FLAG'):"$"::VARCHAR AS end_adj_flag,
    XMLGET(r.raw_xml, 'FIRST_PAY_DT'):"$"::VARCHAR AS first_pay_dt,
    XMLGET(r.raw_xml, 'FIRST_SETTLE_DT'):"$"::VARCHAR AS first_settle_dt,
    XMLGET(r.raw_xml, 'FLAG_144A'):"$"::VARCHAR AS flag_144_a,
    XMLGET(r.raw_xml, 'FLAG_REG_S'):"$"::VARCHAR AS flag_reg_s,
    TRY_TO_DECIMAL(XMLGET(r.raw_xml, 'ISSUE_PRICE'):"$"::VARCHAR, 18, 4) AS issue_price,
    XMLGET(r.raw_xml, 'MATURITY_DT'):"$"::VARCHAR AS maturity_dt,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._ingestion_ts AS _ingestion_ts
FROM RAW.raw_analytics r;

-- Entity `country_classification` (/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_country_classification
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = INCREMENTAL
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_country_classification: child of STAGING.staging_analytics via asset_fk -> STAGING.staging_analytics.asset_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR, a1.index::VARCHAR)) AS country_classification_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR)) AS asset_fk,
    XMLGET(a1.value, 'CNTRY'):"$"::VARCHAR AS cntry,
    XMLGET(a1.value, 'CNTRY_SRC'):"$"::VARCHAR AS cntry_src,
    XMLGET(a1.value, 'CNTRY_TYPE'):"$"::VARCHAR AS cntry_type,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._ingestion_ts AS _ingestion_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(r.raw_xml, 'COUNTRY_CLASSIFICATION_set'), '$')), GET(XMLGET(r.raw_xml, 'COUNTRY_CLASSIFICATION_set'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(r.raw_xml, 'COUNTRY_CLASSIFICATION_set'), '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'COUNTRY_CLASSIFICATION_record';

-- Entity `cusip2` (/ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_cusip2
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = INCREMENTAL
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_cusip2: child of STAGING.staging_analytics via asset_fk -> STAGING.staging_analytics.asset_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR, a1.index::VARCHAR)) AS cusip2_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR)) AS asset_fk,
    XMLGET(a1.value, 'CODE'):"$"::VARCHAR AS code,
    XMLGET(a1.value, 'IDENTIFIER'):"$"::VARCHAR AS identifier,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._ingestion_ts AS _ingestion_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(r.raw_xml, 'CUSIP2_set'), '$')), GET(XMLGET(r.raw_xml, 'CUSIP2_set'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(r.raw_xml, 'CUSIP2_set'), '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'CUSIP2_record';

-- Entity `cusip_alias` (/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_cusip_alias
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = INCREMENTAL
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_cusip_alias: child of STAGING.staging_analytics via asset_fk -> STAGING.staging_analytics.asset_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR, a1.index::VARCHAR)) AS cusip_alias_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, r._record_index::VARCHAR)) AS asset_fk,
    TRY_TO_NUMBER(XMLGET(a1.value, 'CODE'):"$"::VARCHAR, 18, 0) AS code,
    TRY_TO_NUMBER(XMLGET(a1.value, 'IDENTIFIER'):"$"::VARCHAR, 18, 0) AS identifier,
    XMLGET(a1.value, 'PURPOSE'):"$"::VARCHAR AS purpose,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._ingestion_ts AS _ingestion_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(r.raw_xml, 'CUSIP_ALIAS_set'), '$')), GET(XMLGET(r.raw_xml, 'CUSIP_ALIAS_set'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(r.raw_xml, 'CUSIP_ALIAS_set'), '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'CUSIP_ALIAS_record';

-- =============================================================================
-- LAYER 3 (CURATED): ONE DYNAMIC TABLE PER XML ENTITY FROM STAGE (analytics v0.1.0) [Schema: CURATED]
-- Entities: asset, country_classification, cusip2, cusip_alias
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS CURATED;

-- Entity `asset` (/ASSETS/ASSET)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics: root entity asset (PK asset_pk)'
AS
WITH hashed AS (
    SELECT
        asset_pk,
        asof_date,
        create_date,
        records,
        class_val,
        accrual_dt,
        amt_isu,
        announce_dt,
        calc_type,
        call_mandatory,
        call_type,
        cd_instmt_type,
        change_dt,
        compound_flag,
        country,
        coupon_fix,
        coup_freq,
        cpn_type,
        currency,
        cusip,
        cusip_type,
        date_conv,
        desc_instmt,
        end_adj_flag,
        first_pay_dt,
        first_settle_dt,
        flag_144_a,
        flag_reg_s,
        issue_price,
        maturity_dt,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(class_val), ''), COALESCE(TO_VARCHAR(accrual_dt), ''), COALESCE(TO_VARCHAR(amt_isu), ''), COALESCE(TO_VARCHAR(announce_dt), ''), COALESCE(TO_VARCHAR(calc_type), ''), COALESCE(TO_VARCHAR(call_mandatory), ''), COALESCE(TO_VARCHAR(call_type), ''), COALESCE(TO_VARCHAR(cd_instmt_type), ''), COALESCE(TO_VARCHAR(change_dt), ''), COALESCE(TO_VARCHAR(compound_flag), ''), COALESCE(TO_VARCHAR(country), ''), COALESCE(TO_VARCHAR(coupon_fix), ''), COALESCE(TO_VARCHAR(coup_freq), ''), COALESCE(TO_VARCHAR(cpn_type), ''), COALESCE(TO_VARCHAR(currency), ''), COALESCE(TO_VARCHAR(cusip_type), ''), COALESCE(TO_VARCHAR(date_conv), ''), COALESCE(TO_VARCHAR(desc_instmt), ''), COALESCE(TO_VARCHAR(end_adj_flag), ''), COALESCE(TO_VARCHAR(first_pay_dt), ''), COALESCE(TO_VARCHAR(first_settle_dt), ''), COALESCE(TO_VARCHAR(flag_144_a), ''), COALESCE(TO_VARCHAR(flag_reg_s), ''), COALESCE(TO_VARCHAR(issue_price), ''), COALESCE(TO_VARCHAR(maturity_dt), '')), 256) AS _row_hash,
        _ingestion_ts,
        _file_name
    FROM STAGING.staging_analytics
),
changes AS (
    -- keep only rows whose non-timestamp content differs from the previous version
    SELECT *
    FROM hashed
    QUALIFY _row_hash IS DISTINCT FROM LAG(_row_hash) OVER (
        PARTITION BY cusip
        ORDER BY _ingestion_ts ASC, _file_name ASC
    )
)
SELECT
    asset_pk,
        asof_date,
        create_date,
        records,
        class_val,
        accrual_dt,
        amt_isu,
        announce_dt,
        calc_type,
        call_mandatory,
        call_type,
        cd_instmt_type,
        change_dt,
        compound_flag,
        country,
        coupon_fix,
        coup_freq,
        cpn_type,
        currency,
        cusip,
        cusip_type,
        date_conv,
        desc_instmt,
        end_adj_flag,
        first_pay_dt,
        first_settle_dt,
        flag_144_a,
        flag_reg_s,
        issue_price,
        maturity_dt,
    _row_hash,
    _ingestion_ts AS valid_start_time,
    LEAD(_ingestion_ts) OVER (
        PARTITION BY cusip
        ORDER BY _ingestion_ts ASC, _file_name ASC
    ) AS valid_end_time,
    (LEAD(_ingestion_ts) OVER (
        PARTITION BY cusip
        ORDER BY _ingestion_ts ASC, _file_name ASC
    ) IS NULL) AS is_current,
    _file_name AS _source_file
FROM changes;

-- Entity `country_classification` (/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_country_classification
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_country_classification: child of CURATED.curated_analytics via asset_fk -> CURATED.curated_analytics.asset_pk (logical FK)'
AS
SELECT
        country_classification_pk,
        asset_fk,
        cntry,
        cntry_src,
        cntry_type,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(cntry), ''), COALESCE(TO_VARCHAR(cntry_src), ''), COALESCE(TO_VARCHAR(cntry_type), '')), 256) AS _row_hash,
        _ingestion_ts,
        _file_name AS _source_file
FROM STAGING.staging_analytics_country_classification;

-- Entity `cusip2` (/ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_cusip2
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_cusip2: child of CURATED.curated_analytics via asset_fk -> CURATED.curated_analytics.asset_pk (logical FK)'
AS
SELECT
        cusip2_pk,
        asset_fk,
        code,
        identifier,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(code), ''), COALESCE(TO_VARCHAR(identifier), '')), 256) AS _row_hash,
        _ingestion_ts,
        _file_name AS _source_file
FROM STAGING.staging_analytics_cusip2;

-- Entity `cusip_alias` (/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_cusip_alias
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_cusip_alias: child of CURATED.curated_analytics via asset_fk -> CURATED.curated_analytics.asset_pk (logical FK)'
AS
SELECT
        cusip_alias_pk,
        asset_fk,
        code,
        identifier,
        purpose,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(code), ''), COALESCE(TO_VARCHAR(identifier), ''), COALESCE(TO_VARCHAR(purpose), '')), 256) AS _row_hash,
        _ingestion_ts,
        _file_name AS _source_file
FROM STAGING.staging_analytics_cusip_alias;

-- =============================================================================
-- OPERATIONAL TABLES: O3 QUARANTINE & O1 DQ RESULTS [Schema: OPS]
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS OPS;

CREATE TABLE IF NOT EXISTS OPS.quarantine_analytics (
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

CREATE TABLE IF NOT EXISTS OPS.dq_results_analytics (
    check_id            VARCHAR(64)     DEFAULT UUID_STRING(),
    dataset             VARCHAR(128)    NOT NULL,
    file_name           VARCHAR(512)    NOT NULL,
    gate_id             VARCHAR(8)      NOT NULL,
    check_name          VARCHAR(256)    NOT NULL,
    passed              BOOLEAN         NOT NULL,
    details             VARCHAR(2048)   NULL,
    checked_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
);
