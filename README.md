# XML to Snowflake Agent-Assisted Pipeline

An automated, agent-driven data engineering pipeline that onboards raw XML datasets into a Snowflake Data Cloud architecture without requiring pre-existing XSD schemas.

---

## 📁 Repository Structure

The repository is modularized with a global Snowflake bootstrap directory and dataset-level isolation:

```
xml_to_snowflake/
├── snowflake_bootstrap/             # One-time Account-level Snowflake setup
│   ├── account_bootstrap.sql        # RBAC roles, Warehouse (5-min auto-suspend), DB & schemas
│   └── README.md                    # Execution guide for ACCOUNTADMIN
├── datasets/                        # Dataset-level packages
│   └── orders/                      # Example 'orders' dataset package
│       ├── registry/                # C4 Git-versioned Schema Registry (YAMLs, contracts)
│       ├── sql/                     # Compiled Snowflake DDL & monitoring queries
│       ├── samples/                 # Sample XMLs used for C0 Schema Bootstrap
│       ├── drift_samples/           # Test XMLs for Additive and Breaking drift
│       └── README.md                # Dataset documentation
├── src/                             # Core Agent implementations and Web UI
│   ├── agents/                      # A0-A5 & C0-C2 agents
│   ├── ddl_compiler.py              # Snowflake DDL & SCD2 compiler
│   ├── web_app.py                   # Control Plane UI backend
│   └── ui/                          # Web UI dashboard
├── config/                          # Global pipeline settings
├── tests/                           # End-to-end automated test suite
├── requirements.txt                 # Project dependencies
└── .gitignore                       # Git ignore rules
```

---

## 🚀 Quickstart

### 1. Bootstrap Snowflake Account
Run [`snowflake_bootstrap/account_bootstrap.sql`](./snowflake_bootstrap/account_bootstrap.sql) in your Snowflake Worksheet as `ACCOUNTADMIN` to provision:
* `COMPUTE_WH` warehouse (5-minute auto-suspend).
* Roles: `DATA_ENGINEER_ROLE`, `DATA_STEWARD_ROLE`, `DATA_ANALYST_ROLE`, `DATAHUB_READER_ROLE`.
* Database `ENTERPRISE_DW` with schemas `RAW`, `STAGING`, `CURATED`, and `OPS`.

### 2. Deploy or Onboard Datasets
Each dataset inside `datasets/<dataset_name>/` contains its own self-contained schema registry, samples, and compiled SQL files:
* Deploy the dataset DDL: `datasets/<dataset_name>/sql/ddl.sql`
* Run the interactive Control Plane UI:
```bash
pip install -r requirements.txt
python -m src.web_app
```
Open **http://localhost:8765** to review schemas, run quality gates, and manage schema drift.
