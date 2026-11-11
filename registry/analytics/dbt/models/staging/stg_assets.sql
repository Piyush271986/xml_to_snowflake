-- Staging dbt model for assets
{{ config(materialized='view') }}

SELECT
    assets_pk,
    
    asof_date, create_date, records, esg_rating, rating_agency
FROM {{ source('snowflake_dw', 'staging_analytics') }}
