# A5 Smoke Test Report — `analytics` (❌ FAILED)

- **Executed At:** `2026-11-11T15:05:01.422682+00:00`
- **Sample XMLs Tested:** 1
- **Files Passed (G1 + G2 + G3):** 1
- **D2 Raw Rows (`raw_analytics`):** 2
- **D3 Staging Rows (`staging_analytics`):** 4382
- **D4 Curated Active SCD2 Rows (`curated_analytics`):** 2191
- **O3 Quarantine Count (`quarantine_analytics`):** 2 *(must be 0)*

## Gate Verification Summary

| Gate | Check Scope | Result |
|---|---|---|
| **G1: Files** | Arrival, SHA-256 idempotency, XML well-formedness | ❌ FAIL |
| **G2: Contract** | Required XPaths, type casts, flattened row counts | ❌ FAIL |
| **G3: Business** | Primary keys (`order_id`, `line_item_product_code`), ranges, domains | ❌ FAIL |
