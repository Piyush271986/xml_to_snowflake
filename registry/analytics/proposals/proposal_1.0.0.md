# C2 Schema Drift Proposal — `analytics` (`v1.0.0`)

- **Status:** `PENDING_C3_APPROVAL`
- **Created At:** `2026-11-11T16:17:42.326651+00:00`

## Drift Findings

| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |
|---|---|---|---|---|---|---|
| `/ASSETS/ASSET/BND_CORP/AMT_ISU` | `TYPE_INCOMPATIBLE` | **BREAKING** | `NUMBER(18,0)` | `VARCHAR` | `INVALID_NON_NUMERIC_AMOUNT` | `analytics_breaking_drift.xml` |

## Proposed Snowflake DDL Changes

```sql
-- BREAKING: widen amt_isu from NUMBER(18,0) to VARCHAR
ALTER TABLE staging_analytics ALTER COLUMN amt_isu SET DATA TYPE VARCHAR;
```

## Downstream Impact (Read from DataHub at C3)

- Staging Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,STAGING.staging_analytics,PROD)
- Curated SCD2 Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,CURATED.curated_analytics,PROD)
- SLA Dashboard: v_sla_dashboard_analytics
- Data Steward: data-steward@enterprise.io
- Engineering Owner: data-eng@enterprise.io
