-- =============================================================================
-- LAYER 2 (STAGE): ONE DYNAMIC TABLE PER XML ENTITY FROM RAW (analytics v0.3.0) [Schema: STAGING]
-- Entities: assets, asset, country_classification, cusip2, cusip_alias
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS STAGING;

-- Entity `assets` (/ASSETS)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics: root entity assets (PK assets_pk)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256)) AS assets_pk,
    r.raw_xml:"@ASOF_DATE"::VARCHAR AS asof_date,
    r.raw_xml:"@CREATE_DATE"::VARCHAR AS create_date,
    TRY_TO_NUMBER(r.raw_xml:"@RECORDS"::VARCHAR, 18, 0) AS records,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'ASSET'), 'BND_CORP'), 'ESG_RATING'):"$"::VARCHAR AS esg_rating,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'ASSET'), 'BND_CORP'), 'RATING_AGENCY'):"$"::VARCHAR AS rating_agency,
    XMLGET(XMLGET(XMLGET(r.raw_xml, 'ASSET'), 'BND_CORP'), 'SENIORITY_TYPE'):"$"::VARCHAR AS seniority_type,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_analytics r;

-- Entity `asset` (/ASSETS/ASSET)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_asset
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_asset: child of STAGING.staging_analytics via assets_fk -> STAGING.staging_analytics.assets_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS asset_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256)) AS assets_fk,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CLASS'):"$"::VARCHAR AS class_val,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'ACCRUAL_DT'):"$"::VARCHAR AS accrual_dt,
    TRY_TO_NUMBER(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'AMT_ISU'):"$"::VARCHAR, 18, 0) AS amt_isu,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'ANNOUNCE_DT'):"$"::VARCHAR AS announce_dt,
    TRY_TO_NUMBER(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CALC_TYPE'):"$"::VARCHAR, 18, 0) AS calc_type,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CALL_MANDATORY'):"$"::VARCHAR AS call_mandatory,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CALL_TYPE'):"$"::VARCHAR AS call_type,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CD_INSTMT_TYPE'):"$"::VARCHAR AS cd_instmt_type,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CHANGE_DT'):"$"::VARCHAR AS change_dt,
    TRY_TO_NUMBER(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COMPOUND_FLAG'):"$"::VARCHAR, 18, 0) AS compound_flag,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COUNTRY'):"$"::VARCHAR AS country,
    TRY_TO_DECIMAL(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COUPON_FIX'):"$"::VARCHAR, 18, 4) AS coupon_fix,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COUP_FREQ'):"$"::VARCHAR AS coup_freq,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CPN_TYPE'):"$"::VARCHAR AS cpn_type,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CURRENCY'):"$"::VARCHAR AS currency,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP'):"$"::VARCHAR AS cusip,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP_TYPE'):"$"::VARCHAR AS cusip_type,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'DATE_CONV'):"$"::VARCHAR AS date_conv,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'DESC_INSTMT'):"$"::VARCHAR AS desc_instmt,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'END_ADJ_FLAG'):"$"::VARCHAR AS end_adj_flag,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'FIRST_PAY_DT'):"$"::VARCHAR AS first_pay_dt,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'FIRST_SETTLE_DT'):"$"::VARCHAR AS first_settle_dt,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'FLAG_144A'):"$"::VARCHAR AS flag_144_a,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'FLAG_REG_S'):"$"::VARCHAR AS flag_reg_s,
    TRY_TO_DECIMAL(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'ISSUE_PRICE'):"$"::VARCHAR, 18, 4) AS issue_price,
    XMLGET(XMLGET(a1.value, 'BND_CORP'), 'MATURITY_DT'):"$"::VARCHAR AS maturity_dt,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(r.raw_xml, '$')), GET(r.raw_xml, '$'), ARRAY_CONSTRUCT(GET(r.raw_xml, '$')))) a1
WHERE GET(a1.value, '@')::VARCHAR = 'ASSET';

-- Entity `country_classification` (/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_country_classification
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_country_classification: child of STAGING.staging_analytics_asset via asset_fk -> STAGING.staging_analytics_asset.asset_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR, a2.index::VARCHAR)) AS country_classification_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS asset_fk,
    XMLGET(a2.value, 'CNTRY'):"$"::VARCHAR AS cntry,
    XMLGET(a2.value, 'CNTRY_SRC'):"$"::VARCHAR AS cntry_src,
    XMLGET(a2.value, 'CNTRY_TYPE'):"$"::VARCHAR AS cntry_type,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(r.raw_xml, '$')), GET(r.raw_xml, '$'), ARRAY_CONSTRUCT(GET(r.raw_xml, '$')))) a1,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COUNTRY_CLASSIFICATION_set'), '$')), GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COUNTRY_CLASSIFICATION_set'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'COUNTRY_CLASSIFICATION_set'), '$')))) a2
WHERE GET(a1.value, '@')::VARCHAR = 'ASSET'
  AND GET(a2.value, '@')::VARCHAR = 'COUNTRY_CLASSIFICATION_record';

-- Entity `cusip2` (/ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_cusip2
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_cusip2: child of STAGING.staging_analytics_asset via asset_fk -> STAGING.staging_analytics_asset.asset_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR, a2.index::VARCHAR)) AS cusip2_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS asset_fk,
    XMLGET(a2.value, 'CODE'):"$"::VARCHAR AS code,
    XMLGET(a2.value, 'IDENTIFIER'):"$"::VARCHAR AS identifier,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(r.raw_xml, '$')), GET(r.raw_xml, '$'), ARRAY_CONSTRUCT(GET(r.raw_xml, '$')))) a1,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP2_set'), '$')), GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP2_set'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP2_set'), '$')))) a2
WHERE GET(a1.value, '@')::VARCHAR = 'ASSET'
  AND GET(a2.value, '@')::VARCHAR = 'CUSIP2_record';

-- Entity `cusip_alias` (/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record)
CREATE OR REPLACE DYNAMIC TABLE STAGING.staging_analytics_cusip_alias
    TARGET_LAG = '5 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'STAGING.staging_analytics_cusip_alias: child of STAGING.staging_analytics_asset via asset_fk -> STAGING.staging_analytics_asset.asset_pk (logical FK)'
AS
SELECT
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR, a2.index::VARCHAR)) AS cusip_alias_pk,
    MD5(CONCAT_WS('|', r._file_name, r._file_sha256, a1.index::VARCHAR)) AS asset_fk,
    TRY_TO_NUMBER(XMLGET(a2.value, 'CODE'):"$"::VARCHAR, 18, 0) AS code,
    TRY_TO_NUMBER(XMLGET(a2.value, 'IDENTIFIER'):"$"::VARCHAR, 18, 0) AS identifier,
    XMLGET(a2.value, 'PURPOSE'):"$"::VARCHAR AS purpose,
    r._file_name AS _file_name,
    r._file_sha256 AS _file_sha256,
    r._load_ts AS _staged_ts
FROM RAW.raw_analytics r,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(r.raw_xml, '$')), GET(r.raw_xml, '$'), ARRAY_CONSTRUCT(GET(r.raw_xml, '$')))) a1,
    LATERAL FLATTEN(INPUT => IFF(IS_ARRAY(GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP_ALIAS_set'), '$')), GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP_ALIAS_set'), '$'), ARRAY_CONSTRUCT(GET(XMLGET(XMLGET(a1.value, 'BND_CORP'), 'CUSIP_ALIAS_set'), '$')))) a2
WHERE GET(a1.value, '@')::VARCHAR = 'ASSET'
  AND GET(a2.value, '@')::VARCHAR = 'CUSIP_ALIAS_record';
