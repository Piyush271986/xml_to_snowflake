# A5 Smoke Test Report — `enterprise_orders` (✅ PASSED)

- **Executed At:** `2026-11-10T14:55:32.003581+00:00`
- **Sample XMLs Tested:** 1
- **Files Passed (G1 + G2 + G3):** 1
- **D2 Raw Rows (`raw_enterprise_orders`):** 1
- **D3 Staging Rows (`staging_enterprise_orders`):** 5
- **D4 Curated Active SCD2 Rows (`curated_enterprise_orders`):** 5
- **O3 Quarantine Count (`quarantine_enterprise_orders`):** 0 *(must be 0)*

## Gate Verification Summary

| Gate | Check Scope | Result |
|---|---|---|
| **G1: Files** | Arrival, SHA-256 idempotency, XML well-formedness | ✅ PASS |
| **G2: Contract** | Required XPaths, type casts, flattened row counts | ✅ PASS |
| **G3: Business** | Primary keys (`order_id`, `line_item_product_code`), ranges, domains | ✅ PASS |
