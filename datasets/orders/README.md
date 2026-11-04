# Dataset: Orders (`datasets/orders`)

This directory encapsulates all assets, sample data, and schema specifications specific to the **`orders`** dataset.

---

## 📁 Directory Structure

```
datasets/orders/
├── registry/                      # C4 Schema Registry files for 'orders'
│   ├── mapping.yaml               # XPath to Snowflake column & type mappings
│   ├── contract.yaml              # G2 Structural & Type contract assertions
│   ├── quality_rules.yaml         # G3 Business rules, domains & range constraints
│   ├── onboarding_manifest.yaml   # A0 Intake manifest with metadata and owners
│   ├── bootstrap_report.md        # C0 Schema inference report & confidence warnings
│   ├── smoke_test_report.md       # A5 Pipeline smoke test validation results
│   └── proposals/                 # C1/C2 Drift proposals (v0.2.0, v1.0.0, etc.)
├── sql/                           # Compiled Snowflake DDL and queries
│   ├── ddl.sql                    # Full Snowflake DDL (D2-D4, SCD Type 2 MERGE, O1, O3)
│   └── monitoring.sql             # O2 Alert queries & O5 SLA dashboard SQL view
├── samples/                       # 10 Representative sample XML files used for C0 inference
└── drift_samples/                 # Edge cases for drift testing
    ├── order_additive_drift.xml   # Adds optional PromoCode & LoyaltyTier (Auto-applied)
    ├── order_breaking_drift.xml   # Breaking changes (Halts for C3 steward review)
    └── order_malformed.xml        # Malformed syntax (Quarantined at G1)
```
