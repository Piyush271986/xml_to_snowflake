# C2 Schema Drift Proposal — `orders` (`v1.0.0`)

- **Status:** `PENDING_C3_APPROVAL`
- **Created At:** `2026-11-04T12:30:58.670425+00:00`

## Drift Findings

| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |
|---|---|---|---|---|---|---|
| `/Order/TotalOrderValue` | `NEW_OPTIONAL_ELEMENT` | **ADDITIVE** | `-` | `NUMBER(18,4)` | `320.00` | `order_breaking_drift.xml` |
| `/Order/OrderDate` | `MISSING_REQUIRED_ELEMENT` | **BREAKING** | `DATE` | `-` | `-` | `order_breaking_drift.xml` |
| `/Order/TotalAmount` | `MISSING_REQUIRED_ELEMENT` | **BREAKING** | `NUMBER(18,4)` | `-` | `-` | `order_breaking_drift.xml` |
| `/Order/LineItems/LineItem/Quantity` | `TYPE_INCOMPATIBLE` | **BREAKING** | `NUMBER(18,0)` | `VARCHAR` | `TWO` | `order_breaking_drift.xml` |
| `/Order/OrderId` | `TYPE_INCOMPATIBLE` | **BREAKING** | `NUMBER(18,0)` | `VARCHAR` | `ORD-BREAKING-999` | `order_breaking_drift.xml` |

## Proposed Snowflake DDL Changes

```sql
ALTER TABLE staging_orders ADD COLUMN IF NOT EXISTS total_order_value NUMBER(18,4) NULL;
ALTER TABLE curated_orders ADD COLUMN IF NOT EXISTS total_order_value NUMBER(18,4) NULL;
-- BREAKING: drop NOT NULL / required contract on /Order/OrderDate (order_date)
ALTER TABLE staging_orders ALTER COLUMN order_date DROP NOT NULL;
-- BREAKING: drop NOT NULL / required contract on /Order/TotalAmount (total_amount)
ALTER TABLE staging_orders ALTER COLUMN total_amount DROP NOT NULL;
-- BREAKING: widen quantity from NUMBER(18,0) to VARCHAR
ALTER TABLE staging_orders ALTER COLUMN quantity SET DATA TYPE VARCHAR;
-- BREAKING: widen order_id from NUMBER(18,0) to VARCHAR
ALTER TABLE staging_orders ALTER COLUMN order_id SET DATA TYPE VARCHAR;
```

## Downstream Impact (Read from DataHub at C3)

- Staging Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,staging_orders,PROD)
- Curated SCD2 Table: urn:li:dataset:(urn:li:dataPlatform:snowflake,curated_orders,PROD)
- SLA Dashboard: v_sla_dashboard_orders
- Data Steward: data-steward@enterprise.io
- Engineering Owner: data-eng@enterprise.io
