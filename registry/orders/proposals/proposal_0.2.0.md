# C2 Schema Drift Proposal — `orders` (`v0.2.0`)

- **Status:** `AUTO_APPLIED`
- **Created At:** `2026-11-03T17:17:30.101630+00:00`

## Drift Findings

| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |
|---|---|---|---|---|---|---|
| `/Order/LoyaltyTier` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `GOLD` | `order_additive_drift.xml` |
| `/Order/PromoCode` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `VARCHAR` | `AUTUMN25` | `order_additive_drift.xml` |

## Proposed Snowflake DDL Changes

```sql
ALTER TABLE staging_orders ADD COLUMN IF NOT EXISTS loyalty_tier VARCHAR NULL;
ALTER TABLE curated_orders ADD COLUMN IF NOT EXISTS loyalty_tier VARCHAR NULL;
ALTER TABLE staging_orders ADD COLUMN IF NOT EXISTS promo_code VARCHAR NULL;
ALTER TABLE curated_orders ADD COLUMN IF NOT EXISTS promo_code VARCHAR NULL;
```

## Downstream Impact (Read from DataHub at C3)

- Staging Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,staging_orders,PROD)
- Curated SCD2 Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,curated_orders,PROD)
- SLA Dashboard: v_sla_dashboard_orders
- Data Steward: data-steward@enterprise.io
- Engineering Owner: data-eng@enterprise.io
