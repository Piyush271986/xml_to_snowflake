-- =============================================================================
-- LAYER 3 (CURATED): ONE DYNAMIC TABLE PER XML ENTITY FROM STAGE (analytics v0.4.0) [Schema: CURATED]
-- Entities: assets, asset, country_classification, cusip2, cusip_alias, rating
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS CURATED;

-- Entity `assets` (/ASSETS)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics: root entity assets (PK assets_pk)'
AS
WITH versioned AS (
    SELECT
        assets_pk,
        asof_date,
        create_date,
        records,
        esg_rating,
        rating_agency,
        seniority_type,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(asof_date), ''), COALESCE(TO_VARCHAR(create_date), ''), COALESCE(TO_VARCHAR(records), ''), COALESCE(TO_VARCHAR(esg_rating), ''), COALESCE(TO_VARCHAR(rating_agency), ''), COALESCE(TO_VARCHAR(seniority_type), '')), 256) AS _row_hash,
        _staged_ts AS is_valid_start,
        LEAD(_staged_ts) OVER (
            PARTITION BY assets_pk
            ORDER BY _staged_ts ASC
        ) AS is_valid_end,
        CASE
            WHEN LEAD(_staged_ts) OVER (
                PARTITION BY assets_pk
                ORDER BY _staged_ts ASC
            ) IS NULL THEN TRUE
            ELSE FALSE
        END AS is_current,
        _staged_ts AS system_start_time,
        LEAD(_staged_ts) OVER (
            PARTITION BY assets_pk
            ORDER BY _staged_ts ASC
        ) AS system_end_time,
        _file_name AS _source_file
    FROM STAGING.staging_analytics
)
SELECT * FROM versioned;

-- Entity `asset` (/ASSETS/ASSET)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_asset
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_asset: child of CURATED.curated_analytics via assets_fk -> CURATED.curated_analytics.assets_pk (logical FK)'
AS
SELECT
        asset_pk,
        assets_fk,
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
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(class_val), ''), COALESCE(TO_VARCHAR(accrual_dt), ''), COALESCE(TO_VARCHAR(amt_isu), ''), COALESCE(TO_VARCHAR(announce_dt), ''), COALESCE(TO_VARCHAR(calc_type), ''), COALESCE(TO_VARCHAR(call_mandatory), ''), COALESCE(TO_VARCHAR(call_type), ''), COALESCE(TO_VARCHAR(cd_instmt_type), ''), COALESCE(TO_VARCHAR(change_dt), ''), COALESCE(TO_VARCHAR(compound_flag), ''), COALESCE(TO_VARCHAR(country), ''), COALESCE(TO_VARCHAR(coupon_fix), ''), COALESCE(TO_VARCHAR(coup_freq), ''), COALESCE(TO_VARCHAR(cpn_type), ''), COALESCE(TO_VARCHAR(currency), ''), COALESCE(TO_VARCHAR(cusip), ''), COALESCE(TO_VARCHAR(cusip_type), ''), COALESCE(TO_VARCHAR(date_conv), ''), COALESCE(TO_VARCHAR(desc_instmt), ''), COALESCE(TO_VARCHAR(end_adj_flag), ''), COALESCE(TO_VARCHAR(first_pay_dt), ''), COALESCE(TO_VARCHAR(first_settle_dt), ''), COALESCE(TO_VARCHAR(flag_144_a), ''), COALESCE(TO_VARCHAR(flag_reg_s), ''), COALESCE(TO_VARCHAR(issue_price), ''), COALESCE(TO_VARCHAR(maturity_dt), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_analytics_asset;

-- Entity `country_classification` (/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_country_classification
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_country_classification: child of CURATED.curated_analytics_asset via asset_fk -> CURATED.curated_analytics_asset.asset_pk (logical FK)'
AS
SELECT
        country_classification_pk,
        asset_fk,
        cntry,
        cntry_src,
        cntry_type,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(cntry), ''), COALESCE(TO_VARCHAR(cntry_src), ''), COALESCE(TO_VARCHAR(cntry_type), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_analytics_country_classification;

-- Entity `cusip2` (/ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_cusip2
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_cusip2: child of CURATED.curated_analytics_asset via asset_fk -> CURATED.curated_analytics_asset.asset_pk (logical FK)'
AS
SELECT
        cusip2_pk,
        asset_fk,
        code,
        identifier,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(code), ''), COALESCE(TO_VARCHAR(identifier), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_analytics_cusip2;

-- Entity `cusip_alias` (/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_cusip_alias
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_cusip_alias: child of CURATED.curated_analytics_asset via asset_fk -> CURATED.curated_analytics_asset.asset_pk (logical FK)'
AS
SELECT
        cusip_alias_pk,
        asset_fk,
        code,
        identifier,
        purpose,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(code), ''), COALESCE(TO_VARCHAR(identifier), ''), COALESCE(TO_VARCHAR(purpose), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_analytics_cusip_alias;

-- Entity `rating` (/ASSETS/ASSET/BND_CORP/RATING_set/RATING_record)
CREATE OR REPLACE DYNAMIC TABLE CURATED.curated_analytics_rating
    TARGET_LAG = '15 minutes'
    WAREHOUSE = COMPUTE_WH
    REFRESH_MODE = AUTO
    INITIALIZE = ON_CREATE
    COMMENT = 'CURATED.curated_analytics_rating: child of CURATED.curated_analytics_asset via asset_fk -> CURATED.curated_analytics_asset.asset_pk (logical FK)'
AS
SELECT
        rating_pk,
        asset_fk,
        rating_agency,
        rating_rating,
        rating_rating_date,
        SHA2(CONCAT_WS('|', COALESCE(TO_VARCHAR(rating_agency), ''), COALESCE(TO_VARCHAR(rating_rating), ''), COALESCE(TO_VARCHAR(rating_rating_date), '')), 256) AS _row_hash,
        _staged_ts AS system_start_time,
        _file_name AS _source_file
FROM STAGING.staging_analytics_rating;
