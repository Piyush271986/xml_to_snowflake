-- Staging dbt model for cusip2
{{ config(materialized='view') }}

SELECT
    cusip2_pk,
    asset_fk,
    code, identifier
FROM {{ source('snowflake_dw', 'staging_analytics_cusip2') }}
