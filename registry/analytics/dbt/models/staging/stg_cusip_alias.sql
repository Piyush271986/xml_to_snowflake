-- Staging dbt model for cusip_alias
{{ config(materialized='view') }}

SELECT
    cusip_alias_pk,
    asset_fk,
    code, identifier, purpose
FROM {{ source('snowflake_dw', 'staging_analytics_cusip_alias') }}
