-- Staging dbt model for country_classification
{{ config(materialized='view') }}

SELECT
    country_classification_pk,
    asset_fk,
    cntry, cntry_src, cntry_type
FROM {{ source('snowflake_dw', 'staging_analytics_country_classification') }}
