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
