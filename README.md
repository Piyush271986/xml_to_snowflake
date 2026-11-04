# XML to Snowflake Agent-Assisted Pipeline

An automated, agent-driven data engineering pipeline that onboards raw XML datasets into a Snowflake Data Cloud architecture without requiring pre-existing XSD schemas. Features schema bootstrap inference, automated quality gates, Git-versioned schema registry, schema drift detection, DataHub metadata emission, and a web control plane.

---

## 🏛️ Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │             ADLS Gen2 / S3                   │
                      │         (Raw XML Landing Zone)               │
                      └──────────────────────┬───────────────────────┘
                                             │
                                    [G1: Files Gate]
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │              Snowflake (D2)                  │
                      │         raw_<dataset> (VARIANT)              │
                      └──────────────────────┬───────────────────────┘
                                             │  Snowflake Stream
                                             │  & Task
                                   [G2: Contract Gate]
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │              Snowflake (D3)                  │
                      │   staging_<dataset> (LATERAL FLATTEN)        │
                      └──────────────────────┬───────────────────────┘
                                             │
                                   [G3: Business Gate]
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │              Snowflake (D4)                  │
                      │   curated_<dataset> (SCD Type 2 CDC)         │
                      └──────────────────────────────────────────────┘
                                             ▲
                                             │ Failures
                      ┌──────────────────────┴───────────────────────┐
                      │              Snowflake (O3)                  │
                      │            quarantine_<dataset>              │
                      └──────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
xml_to_snowflake/
├── config/
│   └── settings.yaml                # Pipeline, Snowflake, and DataHub configurations
├── sql/
│   ├── bootstrap/
│   │   └── 01_account_bootstrap.sql # Snowflake RBAC, Warehouses, Databases & Schemas
│   └── templates/                   # Reusable Snowflake DDL / Task templates
├── src/
│   ├── agents/
│   │   ├── a0_intake.py             # Stage ①: Intake & validation agent
│   │   ├── c0_bootstrap.py          # Stage ②: Zero-XSD Schema inference agent
│   │   ├── a1_provision.py          # Stage ④: Snowflake DDL & warehouse provisioner
│   │   ├── a2_catalog.py            # Stage ⑤: DataHub catalog & lineage emitter
│   │   ├── a3_quality_gates.py      # Stage ⑥: G1, G2, G3 Quality gate engine
│   │   ├── a4_monitoring.py         # Stage ⑦: Freshness, SLA & O4 runbook generator
│   │   ├── a5_smoke_test.py         # Stage ⑧: End-to-end smoke test validator
│   │   ├── c1_drift_agent.py        # Schema drift detector (Additive vs Breaking)
│   │   └── c2_proposal_agent.py     # C3 approval proposal & auto-apply engine
│   ├── models.py                    # Pydantic data schemas
│   ├── xml_infer.py                 # Core XML XPath discovery & narrowest type ladder
│   ├── ddl_compiler.py              # Snowflake SQL, LATERAL FLATTEN & SCD2 compiler
│   ├── web_app.py                   # Control Plane UI backend (Starlette/FastAPI)
│   ├── push_to_datahub.py           # DataHub REST integration script
│   └── ui/
│       └── index.html               # 10-Stage interactive Web Dashboard
├── registry/                        # C4 Git-Versioned Schema Registry
│   └── orders/
│       ├── mapping.yaml             # XPath to Snowflake column & type mappings
│       ├── contract.yaml            # Structural assertions (G2)
│       ├── quality_rules.yaml       # Business domain & range checks (G3)
│       └── ddl.sql                  # Compiled Snowflake DDL for pipeline
├── samples/                         # Sample and drift test XML files
└── tests/
    └── test_pipeline_e2e.py         # Comprehensive unit and integration test suite
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Snowflake Account
- Docker (optional, for local DataHub metadata catalog)

### 2. Setup Snowflake Account & RBAC
Run the bootstrap script as `ACCOUNTADMIN` in your Snowflake worksheet:
```sql
-- Located at: sql/bootstrap/01_account_bootstrap.sql
```
This provisions:
- `COMPUTE_WH` warehouse (with 5-minute auto-suspend)
- Roles: `DATA_ENGINEER_ROLE`, `DATA_STEWARD_ROLE`, `DATA_ANALYST_ROLE`, `DATAHUB_READER_ROLE`
- Database: `ENTERPRISE_DW` with schemas `RAW`, `STAGING`, `CURATED`, and `OPS`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Pipeline & UI
Start the Control Plane dashboard locally:
```bash
python -m src.web_app
```
Access the dashboard at: `http://localhost:8765`

### 5. Run Automated Tests
```bash
python -m unittest discover -s tests -v
```
