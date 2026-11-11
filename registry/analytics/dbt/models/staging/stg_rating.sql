-- Staging dbt model for rating
{{ config(materialized='view') }}

SELECT
    rating_pk,
    asset_fk,
    rating_agency, rating_rating, rating_rating_date
FROM {{ source('snowflake_dw', 'staging_analytics_rating') }}
