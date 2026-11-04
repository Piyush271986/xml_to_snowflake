# A5 Smoke Test Report — `orders` (✅ PASSED)

- **Executed At:** `2026-11-04T12:29:15.318929+00:00`
- **Sample XMLs Tested:** 10
- **Files Passed (G1 + G2 + G3):** 10
- **D2 Raw Rows (`raw_orders`):** 10
- **D3 Staging Rows (`staging_orders`):** 15
- **D4 Curated Active SCD2 Rows (`curated_orders`):** 15
- **O3 Quarantine Count (`quarantine_orders`):** 0 *(must be 0)*

## Gate Verification Summary

| Gate | Check Scope | Result |
|---|---|---|
| **G1: Files** | Arrival, SHA-256 idempotency, XML well-formedness | ✅ PASS |
| **G2: Contract** | Required XPaths, type casts, flattened row counts | ✅ PASS |
| **G3: Business** | Primary keys (`order_id`, `line_item_product_code`), ranges, domains | ✅ PASS |
