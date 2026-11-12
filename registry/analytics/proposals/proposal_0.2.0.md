# C2 Schema Drift Proposal — `analytics` (`v0.2.0`)

- **Status:** `AUTO_APPLIED`
- **Created At:** `2026-11-12T13:22:54.326520+00:00`

## Drift Findings

| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |
|---|---|---|---|---|---|---|
| `/ASSETS/ASSET/BND_CORP/ESG_RATING` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `AAA` | `analytics_additive_drift.xml` |
| `/ASSETS/ASSET/BND_CORP/RATING_AGENCY` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `MSCI` | `analytics_additive_drift.xml` |

## Proposed Snowflake DDL Changes

```sql
-- Additive drift column for Dynamic Table staging_analytics: esg_rating (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_analytics REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_analytics REFRESH;
-- Additive drift column for Dynamic Table staging_analytics: rating_agency (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_analytics REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_analytics REFRESH;
```

## Downstream Impact (Read from DataHub at C3)

- Staging Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,STAGING.staging_analytics,PROD)
- Curated SCD2 Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,CURATED.curated_analytics,PROD)
- SLA Dashboard: v_sla_dashboard_analytics
- Data Steward: data-steward@enterprise.io
- Engineering Owner: data-eng@enterprise.io
