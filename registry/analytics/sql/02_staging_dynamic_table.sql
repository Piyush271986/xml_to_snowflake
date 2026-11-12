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
