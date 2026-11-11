-- Staging dbt model for asset
{{ config(materialized='view') }}

SELECT
    asset_pk,
    assets_fk,
    class_val, accrual_dt, amt_isu, announce_dt, calc_type, call_mandatory, call_type, cd_instmt_type, change_dt, compound_flag, country, coupon_fix, coup_freq, cpn_type, currency, cusip, cusip_type, date_conv, desc_instmt, end_adj_flag, first_pay_dt, first_settle_dt, flag_144_a, flag_reg_s, issue_price, maturity_dt
FROM {{ source('snowflake_dw', 'staging_analytics_asset') }}
