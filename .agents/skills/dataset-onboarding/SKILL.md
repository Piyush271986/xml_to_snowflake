---
name: dataset-onboarding
description: >-
  Standardized runbook and procedures to onboard new XML datasets into the Snowflake
  Medallion Data Lakehouse (RAW Normal Table + Snowpipe -> STAGING Dynamic Tables with child
  hierarchy explosion & FK relationships -> CURATED Dynamic Tables with SCD Type 2 history).
  Enforces mandatory C3 Human Approval Gates (YAML Schema / ER Model review & Go-Live sign-off)
  matching the Control Plane UI.
---

# XML Dataset Onboarding Skill

This skill guides the agent through onboarding a new XML dataset into Snowflake using the multi-agent pipeline (`xml_to_snowflake`).

---

## 🏗️ Architecture & Modeling Principles

1. **3-Layer Medallion Architecture**:
   - **Layer 1 (RAW)**: Normal Table loaded via Snowpipe (`@RAW.ADLS_XML_STAGE/<dataset>/`), storing immutable payload as `VARIANT` (`raw_xml`).
   - **Layer 2 (STAGING)**: Snowflake Dynamic Tables (`TARGET_LAG = '5 minutes'`). **Explodes every repeating XML child element into its own separate table** (e.g. `<ASSET>` &rarr; `staging_<ds>`, `<CUSIP2_record>` &rarr; `staging_<ds>_cusip2`).
   - **Layer 3 (CURATED / GOLD)**: Snowflake Dynamic Tables (`TARGET_LAG = '15 minutes'`). Root entity tracks SCD Type 2 history; child entities mirror parent keys with foreign keys.
2. **Surrogate PK/FK Linking**:
   - Every entity receives a deterministic surrogate primary key: `<entity>_pk = MD5(CONCAT_WS('|', _file_name, _file_sha256, indices...))`.
   - Child tables include `<parent>_fk` referencing `<parent>_pk`.
3. **Mandatory Human Approval Gates**:
   - **Gate 1 (C3 Schema & Model Approval)**: MUST inspect and present the 3-layer YAML schemas, field inventory, and Mermaid ER diagram **BEFORE** generating DDL SQL.
   - **Gate 2 (C3 Go-Live Sign-Off)**: MUST verify A5 smoke test passes with 0 quarantine records before connecting to Snowflake via External Browser SSO.

---

## 📋 Standard Onboarding Workflow

### Step 1: Intake & Hierarchical Schema Inference (A0 & Step 1 Agent)
Run the intake and inference pipeline to generate the YAML specifications:

```powershell
Set-Location c:\Databricks_project\xml_to_snowflake
python -c "
from pathlib import Path
from src.agents.a0_intake import run_a0_intake
from src.agents.c0_bootstrap import run_data_steward_agent

dataset = '<dataset_name>'  # e.g. 'analytics' or 'orders'
sample_dir = Path('samples/' + dataset)  # or 'datasets/<dataset>/samples'
reg_root = Path('registry')

manifest = run_a0_intake(
    dataset=dataset,
    source_system='source_' + dataset,
    sample_dir=sample_dir,
    registry_root=reg_root,
    adls_landing_path='abfss://landing@adls.dfs.core.windows.net/xml/' + dataset + '/',
)
mapping = run_data_steward_agent(manifest=manifest, registry_root=reg_root)
print(f'Successfully bootstrapped {dataset}: {len(mapping.fields)} fields inferred.')
"
```

This generates in `registry/<dataset>/`:
- `raw_schema.yaml`
- `staging_schema.yaml` (one table per parent + child hierarchy)
- `gold_schema.yaml`
- `data_model.yaml` (includes Mermaid ER diagram string)
- `contract.yaml` (G2 contract rules)
- `quality_rules.yaml` (G3 business rules)

---

### 🛑 HUMAN APPROVAL GATE 1: C3 Data Model & Schema Review

> [!IMPORTANT]
> **DO NOT generate DDL or deploy to Snowflake without explicit user confirmation.**
> Present the following to the user:
> 1. Summary of identified entities (parent table & child tables).
> 2. Primary Key (`<parent>_pk`) and Foreign Key (`<parent>_fk`) mappings.
> 3. The Mermaid ER diagram from `data_model.yaml`.
> 4. Any low-confidence fields (< 0.8) or suggested renames.
> 
> Ask the user: *"Do you approve the proposed data model and YAML schemas to proceed to Step 2 DDL generation?"*

---

### Step 2: DDL Compilation (Step 2 Agent)
Once the user approves Gate 1:

```powershell
Set-Location c:\Databricks_project\xml_to_snowflake
python -c "
from pathlib import Path
from src.orchestrator import approve_c3_schema_review
from src.agents.ddl_generator_agent import run_ddl_generator_agent

dataset = '<dataset_name>'
reg_root = Path('registry')

approve_c3_schema_review(dataset=dataset, registry_root=reg_root)
manifest = run_ddl_generator_agent(dataset=dataset, registry_root=reg_root)
print('DDL Generated in sql/:', list(manifest.sql_artifacts.keys()))
"
```

This compiles:
- `sql/01_raw_snowpipe.sql`
- `sql/02_staging_dynamic_table.sql` (separate `CREATE OR REPLACE DYNAMIC TABLE` for each entity)
- `sql/03_gold_dynamic_table.sql`
- `sql/04_ops_quarantine_dq.sql`
- `ddl.sql` (master script)

---

### Step 3: Local Provisioning & Smoke Testing (A1–A5 Agents)
Deploy to local simulation warehouse to run end-to-end verification through G1, G2, and G3 gates:

```powershell
Set-Location c:\Databricks_project\xml_to_snowflake
python -c "
from pathlib import Path
from src.agents.a1_provision import run_a1_provision
from src.agents.a2_catalog import run_a2_catalog
from src.agents.a3_quality_gates import deploy_a3_quality_gates
from src.agents.a4_monitoring import run_a4_monitoring
from src.agents.a5_smoke_test import run_a5_smoke_test

dataset = '<dataset_name>'
reg_root = Path('registry')

run_a1_provision(dataset, reg_root)
run_a2_catalog(dataset, reg_root)
deploy_a3_quality_gates(dataset, reg_root)
run_a4_monitoring(dataset, reg_root)
smoke = run_a5_smoke_test(dataset, reg_root)
print('Smoke Test Result:', smoke)
"
```

---

### 🛑 HUMAN APPROVAL GATE 2: C3 Go-Live & Snowflake Deployment

> [!IMPORTANT]
> Verify that `quarantine_open_rows == 0` and `smoke_test_passed == True`.
> Present the smoke test report (`registry/<dataset>/smoke_test_report.md`) to the user.
> 
> Ask the user: *"Smoke test passed with 0 quarantined rows. Would you like to deploy live to Snowflake via External Browser SSO?"*

Once confirmed, deploy to Snowflake:

```powershell
Set-Location c:\Databricks_project\xml_to_snowflake
python -c "
from pathlib import Path
from src.orchestrator import approve_c3_go_live

dataset = '<dataset_name>'
reg_root = Path('registry')

res = approve_c3_go_live(
    dataset=dataset,
    registry_root=reg_root,
    deploy_to_snowflake=True,
    signoff_notes='User approved after verifying hierarchical model and A5 smoke test.',
)
print('Live Deployment Completed:', res.get('snowflake_live_deployment', {}).get('status'))
"
```

---

## 🔍 Troubleshooting & Special Cases

- **Web UI Control**:
  - To launch or inspect via Web UI: `python -m src.web_app` at `http://127.0.0.1:8765`.
- **Duplicate Keys**:
  - If `<parent>_pk` or business keys have duplicates in test XMLs, check G3 quality rules in `registry/<dataset>/quality_rules.yaml`.
- **Schema Drift**:
  - If new XML tags arrive at runtime, the C1 Drift Agent detects them and proposes additive changes automatically.

