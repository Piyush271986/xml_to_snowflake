# Step 1: Data Steward & Modeling Report — `analytics`

> **Status:** Pending Human Approval (`PENDING_HUMAN_APPROVAL`). **No SQL DDL has been generated yet.**
> Once approved at C3, the **DDL Generator Agent (Step 2)** will compile the Snowpipe and Dynamic Table SQLs.

## Proposed 3-Layer Medallion Data Model (YAML Schemas)

| Layer | YAML Schema File | Table Name | Snowflake Object Type | Ingestion / Refresh |
|---|---|---|---|---|
| **1. RAW** | `raw_schema.yaml` | `raw_analytics` | `NORMAL_TABLE` | `SNOWPIPE` (`ADLS -> RAW`) |
| **2. STAGE** | `staging_schema.yaml` | `staging_analytics` | `DYNAMIC_TABLE` (`TARGET_LAG = '5 minutes'`) | `DYNAMIC_TABLE_REFRESH` (`RAW -> STAGE`) |
| **3. GOLD** | `gold_schema.yaml` | `curated_analytics` | `DYNAMIC_TABLE` (`TARGET_LAG = '15 minutes'`) | `DYNAMIC_TABLE_REFRESH` (`STAGE -> GOLD`) |

- **Samples Analyzed:** 1 valid XML files
- **Root Element:** `/ASSETS`
- **Inferred Business Keys:** `asset_cusip`
- **Total Inferred Fields:** 40 (37 array fields)
- **Low-Confidence Fields (< 0.8):** 0

## Inferred Field Inventory

| XPath | Column | Snowflake Type | Required | Array (`LATERAL FLATTEN`) | Confidence | Status |
|---|---|---|---|---|---|---|
| `/ASSETS/@ASOF_DATE` | `asof_date` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/ASSETS/@CREATE_DATE` | `create_date` | `VARCHAR` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/ASSETS/@RECORDS` | `records` | `NUMBER(18,0)` | `True` | `False` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CLASS` | `asset_class` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/ACCRUAL_DT` | `asset_accrual_dt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/AMT_ISU` | `asset_amt_isu` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/ANNOUNCE_DT` | `asset_announce_dt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CALC_TYPE` | `asset_calc_type` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CALL_MANDATORY` | `asset_call_mandatory` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CALL_TYPE` | `asset_call_type` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CD_INSTMT_TYPE` | `asset_cd_instmt_type` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CHANGE_DT` | `asset_change_dt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COMPOUND_FLAG` | `asset_compound_flag` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUNTRY` | `asset_country` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/@SIZE` | `country_classification_set_size` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record/CNTRY` | `country_classification_record_cntry` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record/CNTRY_SRC` | `country_classification_record_cntry_src` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record/CNTRY_TYPE` | `country_classification_record_cntry_type` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUPON_FIX` | `asset_coupon_fix` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/COUP_FREQ` | `asset_coup_freq` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CPN_TYPE` | `asset_cpn_type` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CURRENCY` | `asset_currency` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP` | `asset_cusip` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP2_set/@SIZE` | `cusip2_set_size` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record/CODE` | `cusip2_record_code` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record/IDENTIFIER` | `cusip2_record_identifier` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/@SIZE` | `cusip_alias_set_size` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record/CODE` | `cusip_alias_record_code` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record/IDENTIFIER` | `cusip_alias_record_identifier` | `NUMBER(18,0)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record/PURPOSE` | `cusip_alias_record_purpose` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/CUSIP_TYPE` | `asset_cusip_type` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/DATE_CONV` | `asset_date_conv` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/DESC_INSTMT` | `asset_desc_instmt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/END_ADJ_FLAG` | `asset_end_adj_flag` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/FIRST_PAY_DT` | `asset_first_pay_dt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/FIRST_SETTLE_DT` | `asset_first_settle_dt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/FLAG_144A` | `asset_flag_144_a` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/FLAG_REG_S` | `asset_flag_reg_s` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/ISSUE_PRICE` | `asset_issue_price` | `NUMBER(18,4)` | `True` | `True` | `1.00` | ✅ High Confidence |
| `/ASSETS/ASSET/BND_CORP/MATURITY_DT` | `asset_maturity_dt` | `VARCHAR` | `True` | `True` | `1.00` | ✅ High Confidence |

## Modeling Engine

- **Engine:** Rule-based. Claude not used (ANTHROPIC_API_KEY not set or llm.enabled=false); rule-based model generated.
