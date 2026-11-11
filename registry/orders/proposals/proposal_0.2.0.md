# C2 Schema Drift Proposal — `orders` (`v0.2.0`)

- **Status:** `AUTO_APPLIED`
- **Created At:** `2026-11-11T03:13:44.763765+00:00`

## Drift Findings

| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |
|---|---|---|---|---|---|---|
| `/Order/LoyaltyTier` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `GOLD` | `order_additive_drift.xml` |
| `/Order/PromoCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `AUTUMN25` | `order_additive_drift.xml` |

## Proposed Snowflake DDL Changes

```sql
-- Additive drift column for Dynamic Table staging_orders: loyalty_tier (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
-- Additive drift column for Dynamic Table staging_orders: promo_code (VARCHAR)
ALTER DYNAMIC TABLE IF EXISTS staging_orders REFRESH;
ALTER DYNAMIC TABLE IF EXISTS curated_orders REFRESH;
```

## Downstream Impact (Read from DataHub at C3)

- Staging Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,staging_orders,PROD)
- Curated SCD2 Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,curated_orders,PROD)
- SLA Dashboard: v_sla_dashboard_orders
- Data Steward: data-steward@enterprise.io
- Engineering Owner: data-eng@enterprise.io
