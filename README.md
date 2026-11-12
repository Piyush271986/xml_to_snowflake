# XML to Snowflake Agent-Assisted Pipeline

An automated, agent-driven data engineering platform that onboards complex, hierarchical raw XML datasets into a Snowflake Medallion Lakehouse architecture without requiring pre-existing XSD schemas or external transformation frameworks (like dbt).

🔗 **Architecture Board:** [Miro — XML to Snowflake Pipeline Architecture](https://miro.com/app/board/uXjVETJagXI=/)

---

## 🌟 Key Features

1. **Deterministic Hierarchical Decomposition (No "One Big Flat Table")**:
   - Rather than forcing nested XML documents into a single wide flat table, the engine deterministically identifies repeating XML entities (e.g. `<ASSET>`, `<CUSIP2_record>`, `<COUNTRY_CLASSIFICATION_record>`, `<CUSIP_ALIAS_record>`, `<LineItem>`) and explodes each child hierarchy into its own relational table across **STAGING** and **CURATED** layers.
   - Automatically generates deterministic MD5 surrogate primary keys (`<entity>_pk`) and links child tables to their parent via explicit foreign keys (`<parent>_fk` &rarr; `<parent>_pk`).

2. **Pure 3-Layer Snowflake Medallion Architecture (No dbt Required)**:
   - **Layer 1 (`RAW` schema)**: Normal table (`RAW.raw_<dataset>`) loaded via Snowpipe (`RAW.pipe_<dataset>`) from ADLS (`@RAW.ADLS_XML_STAGE/<dataset>/`), storing immutable raw XML payloads in Snowflake `VARIANT` (`raw_xml`).
   - **Layer 2 (`STAGING` schema)**: Declarative Snowflake Dynamic Tables (`TARGET_LAG = '5 minutes'`) executing typed `XMLGET` + `LATERAL FLATTEN` extraction for the root entity and every child entity (`STAGING.staging_<dataset>`, `STAGING.staging_<dataset>_<child>`).
   - **Layer 3 (`CURATED` schema)**: Declarative Snowflake Dynamic Tables (`TARGET_LAG = '15 minutes'`) with automated SCD Type 2 version history (`is_valid_start`, `is_valid_end`, `is_current`) on the root entity and foreign-keyed child Dynamic Tables (`CURATED.curated_<dataset>_<child>`).
   - **Operations (`OPS` schema)**: Houses `OPS.quarantine_<dataset>`, `OPS.dq_results_<dataset>`, and the `OPS.v_sla_dashboard_<dataset>` monitoring view.

3. **Mandatory C3 Human Approval Gates & Visual ER Diagram**:
   - **Gate 1 (Schema & Model Approval)**: Mandatory review step before any SQL DDL is generated. Data Stewards inspect the 3-layer YAML specifications (`raw_schema.yaml`, `staging_schema.yaml`, `gold_schema.yaml`, `data_model.yaml`) alongside an interactive **Mermaid ER Diagram** showing all parent-child tables and `1:N` foreign key relationships.
   - **Gate 2 (Go-Live Sign-Off)**: Mandatory sign-off after passing A5 Smoke Testing (`quarantine_open_rows == 0`) before deploying live to Snowflake via External Browser SSO.

4. **In-Stream Quality Gates (A3) & Self-Healing Schema Drift (C1/C2)**:
   - **G1 Files Gate (ADLS &rarr; RAW)**: File non-empty check, SHA-256 idempotency deduplication, and XML well-formedness.
   - **G2 Contract Gate (RAW &rarr; STAGING)**: Required XPaths, Snowflake type cast compatibility, row count bounds, and unknown element detection.
   - **G3 Business Gate (STAGING &rarr; CURATED)**: Primary key uniqueness, non-null assertions, accepted value domains, and numeric range checks.
   - **C1 Drift & C2 Proposal Agents**: Non-breaking additive elements auto-apply; breaking changes route to `OPS.quarantine_<dataset>` and generate C2 mitigation proposals for C3 human review.

5. **Antigravity Custom Workspace Skill (`/dataset-onboarding`)**:
   - Project-scoped skill at [`.agents/skills/dataset-onboarding/SKILL.md`](./.agents/skills/dataset-onboarding/SKILL.md) that guides you interactively through onboarding any new XML dataset with built-in C3 human approval gates.

---

## 📁 Repository Structure

```text
xml_to_snowflake/
├── .agents/                         # Antigravity workspace customizations
│   ├── skills/
│   │   └── dataset-onboarding/      # Guided interactive XML dataset onboarding skill
│   │       └── SKILL.md
│   ├── rules/                       # Project rules (graphify knowledge graph sync)
│   └── workflows/                   # Standard operational workflows
├── config/                          # Global pipeline, LLM, DataHub & Snowflake settings
│   └── settings.yaml
├── datasets/                        # Dataset packages (samples, schemas, SQL)
│   ├── analytics/                   # Corporate bond (<ASSET>/<BND_CORP>) hierarchical dataset
│   ├── enterprise_orders/           # Enterprise purchase orders
│   └── orders/                      # Core orders dataset package
├── registry/                        # C4 Git-versioned Schema Registry per dataset
│   └── <dataset>/
│       ├── raw_schema.yaml          # Layer 1 Normal Table specification (RAW schema)
│       ├── staging_schema.yaml      # Layer 2 Dynamic Table specs (parent + child entities)
│       ├── gold_schema.yaml         # Layer 3 Curated Dynamic Table specs (SCD2 + FKs)
│       ├── data_model.yaml          # Medallion data model, FK relationships & Mermaid ER diagrams
│       ├── mapping.yaml             # Canonical field inventory & XPath expressions
│       ├── contract.yaml            # G2 Contract specification
│       ├── quality_rules.yaml       # G3 Business quality rules
│       ├── sql/                     # Step 2 generated SQL scripts per layer
│       │   ├── 01_raw_snowpipe.sql
│       │   ├── 02_staging_dynamic_table.sql
│       │   ├── 03_gold_dynamic_table.sql
│       │   └── 04_ops_quarantine_dq.sql
│       └── ddl.sql                  # Consolidated master Snowflake DDL
├── samples/                         # Raw sample & drift XML files
├── snowflake_bootstrap/             # One-time Account-level Snowflake setup
│   ├── account_bootstrap.sql        # RBAC roles, Warehouse, Database & 4 Schemas (RAW, STAGING, CURATED, OPS)
│   └── README.md
├── src/                             # Core Agent implementations and Control Plane Web UI
│   ├── agents/                      # Multi-agent pipeline (A0–A5, C0–C2, Step 2 DDL Generator)
│   │   ├── a0_intake.py             # XML discovery & sample validation
│   │   ├── c0_bootstrap.py          # Step 1: Data Steward & 3-layer hierarchical modeling agent
│   │   ├── ddl_generator_agent.py   # Step 2: Snowflake DDL compilation agent
│   │   ├── a1_provision.py          # Step 3: Deployment & local warehouse simulator
│   │   ├── a2_catalog.py            # DataHub metadata & lineage emitter
│   │   ├── a3_quality_gates.py      # G1, G2, G3 runtime quality gate evaluator
│   │   ├── a4_monitoring.py         # O2/O5 SLA views & operational monitoring
│   │   ├── a5_smoke_test.py         # End-to-end smoke test runner
│   │   ├── c1_drift_agent.py        # Schema drift detector
│   │   └── c2_proposal_agent.py     # Drift mitigation proposer
│   ├── entity_model.py              # Parent/child XML entity decomposition & Mermaid ER generator
│   ├── ddl_compiler.py              # Snowflake Snowpipe & multi-entity Dynamic Table DDL compiler
│   ├── xml_infer.py                 # XML XPath discovery & narrowest Snowflake type ladder
│   ├── snowflake_client.py          # Snowflake connector (External Browser SSO & live deployment)
│   ├── web_app.py                   # Starlette/Uvicorn Control Plane UI backend
│   └── ui/                          # Web UI dashboard with interactive Mermaid ER viewer
├── tests/                           # End-to-end automated unit & regression test suite
├── requirements.txt                 # Python dependencies
└── README.md
```

---

## 🚀 Quickstart

### 1. Prerequisites
Install required Python packages:
```bash
pip install -r requirements.txt
```

### 2. Bootstrap Snowflake (One-Time)
Run [`snowflake_bootstrap/account_bootstrap.sql`](./snowflake_bootstrap/account_bootstrap.sql) in Snowflake as `ACCOUNTADMIN` to provision:
- Warehouse: `COMPUTE_WH` (5-minute auto-suspend)
- Roles: `DATA_ENGINEER_ROLE`, `DATA_STEWARD_ROLE`, `DATA_ANALYST_ROLE`, `DATAHUB_READER_ROLE`
- Database: `ENTERPRISE_DW`
- Schemas: `RAW`, `STAGING`, `CURATED`, and `OPS`

### 3. Option A — Onboard via the Control Plane Web UI
Start the web dashboard:
```bash
python -m src.web_app
```
Open **[http://127.0.0.1:8765](http://127.0.0.1:8765)** to:
1. Run **Step 1 (Data Steward Agent)** on sample XML files to generate 3-layer YAML schemas (no DDL yet).
2. Inspect the **Proposed Data Model Diagram (Mermaid ER)** in **Tab ②** showing parent and child tables (`staging_<ds>` and `staging_<ds>_<child>`) linked via `<parent>_fk` &rarr; `<parent>_pk`.
3. Approve the YAMLs at **C3 Gate 1** to trigger **Step 2 (DDL Generator Agent)** and **Step 3 (Pipeline Deployment + A2–A5 Smoke Test)**.
4. Review the A5 Smoke Test report in **Tab ⑤** (**C3 Gate 2**) and deploy live to Snowflake via External Browser SSO.

### 4. Option B — Onboard via the `/dataset-onboarding` AI Skill
In the chat interface, invoke:
```text
/dataset-onboarding
```
The agent will execute the same gated workflow interactively in chat — presenting the parent/child table breakdown and Mermaid ER diagram at **Gate 1** before compiling SQLs, running the A5 smoke test, and pausing at **Gate 2** before live Snowflake deployment.
