# XML to Snowflake Agent-Assisted Pipeline

An automated, agent-driven data engineering platform that onboards complex, hierarchical raw XML datasets into a Snowflake Medallion Lakehouse architecture without requiring pre-existing XSD schemas.

---

## 🌟 Key Features

1. **Deterministic Hierarchical Decomposition (No "One Big Flat Table")**:
   - Rather than forcing nested XML documents into a single wide table, the engine deterministically identifies repeating XML entities (e.g. `<ASSET>` vs `<CUSIP2_record>`, `<LineItem>`) and explodes them into distinct tables across **STAGING** and **CURATED** layers.
   - Automatically establishes surrogate primary keys (`<entity>_pk`) and foreign keys (`<parent>_fk` &rarr; `<parent>_pk`) with deterministic MD5 indexing.

2. **3-Layer Snowflake Medallion Architecture**:
   - **Layer 1 (RAW)**: Normal table loaded via Snowpipe from ADLS (`@RAW.ADLS_XML_STAGE/<dataset>/`), storing immutable raw XML payloads in Snowflake `VARIANT` (`raw_xml`).
   - **Layer 2 (STAGING)**: Declarative Snowflake Dynamic Tables (`TARGET_LAG = '5 minutes'`) executing typed `XMLGET` extraction and relational normalization.
   - **Layer 3 (CURATED / GOLD)**: Declarative Snowflake Dynamic Tables (`TARGET_LAG = '15 minutes'`) with automated SCD Type 2 history tracking on root business keys and relational foreign key linking on child entities.

3. **Mandatory C3 Human Approval Gates**:
   - **Gate 1 (Schema & Model Approval)**: Mandatory review step before DDL generation. Inspect 3-layer YAML specifications (`raw_schema.yaml`, `staging_schema.yaml`, `gold_schema.yaml`, `data_model.yaml`) and an interactive **Mermaid ER Diagram** showing parent-child table relationships.
   - **Gate 2 (Go-Live Sign-Off)**: Mandatory sign-off after passing A5 Smoke Testing (0 quarantine records) before deploying live to Snowflake via External Browser SSO.

4. **Self-Healing Schema Drift & Quality Gates**:
   - **G1 Files Gate**: SHA-256 idempotency & XML well-formedness.
   - **G2 Contract Gate**: Required XPaths & expected row counts.
   - **G3 Business Gate**: Primary key uniqueness, ranges, and domain checks.
   - **C1 Drift Agent**: Differentiates between non-breaking additive fields (auto-applied) and breaking changes (quarantine + C3 review).

5. **Antigravity Custom Workspace Skill**:
   - Native `/dataset-onboarding` skill located at `.agents/skills/dataset-onboarding/SKILL.md` to run interactive guided dataset onboarding directly within your AI assistant.

---

## 📁 Repository Structure

```
xml_to_snowflake/
├── .agents/                         # Antigravity agent customizations
│   ├── skills/                      # Workspace skills
│   │   └── dataset-onboarding/      # Guided interactive XML dataset onboarding skill
│   │       └── SKILL.md
│   ├── rules/                       # Coding & project rules (e.g. graphify)
│   └── workflows/                   # Standard operational workflows
├── config/                          # Pipeline & Snowflake connection settings
│   └── settings.yaml
├── datasets/                        # Dataset packages (samples, schemas, SQL)
│   ├── analytics/                   # Analytics investment bond sample dataset
│   ├── enterprise_orders/           # Enterprise purchase orders
│   └── orders/                      # Core orders dataset package
├── registry/                        # C4 Git-versioned Schema Registry per dataset
│   ├── <dataset>/
│   │   ├── raw_schema.yaml          # Layer 1 table specification
│   │   ├── staging_schema.yaml      # Layer 2 Dynamic Table specs (parent + child entities)
│   │   ├── gold_schema.yaml         # Layer 3 Curated Dynamic Table specs
│   │   ├── data_model.yaml          # Medallion data model & Mermaid ER diagram
│   │   ├── mapping.yaml             # Canonical field inventory & XPaths
│   │   ├── contract.yaml            # G2 Contract specification
│   │   ├── quality_rules.yaml       # G3 Business quality rules
│   │   ├── sql/                     # Layered SQL artifacts (01_raw, 02_staging, 03_gold, 04_ops)
│   │   └── ddl.sql                  # Master compiled Snowflake DDL
├── samples/                         # Raw test XML files (e.g. analytics.xml, order_001.xml)
├── snowflake_bootstrap/             # One-time Account-level Snowflake setup
│   ├── account_bootstrap.sql        # RBAC roles, Warehouse, Database & 4 Schemas (RAW, STAGING, CURATED, OPS)
│   └── README.md
├── src/                             # Core Agent implementations and Web UI
│   ├── agents/                      # A0-A5 & C0-C2 multi-agent system
│   │   ├── a0_intake.py             # XML discovery & sample validation
│   │   ├── c0_bootstrap.py          # Step 1: Data Steward & 3-layer modeling agent
│   │   ├── ddl_generator_agent.py   # Step 2: Snowflake DDL compilation agent
│   │   ├── a1_provision.py          # Step 3: Deployment & local warehouse simulator
│   │   ├── a2_catalog.py            # DataHub metadata & lineage emitter
│   │   ├── a3_quality_gates.py      # G1, G2, G3 quality evaluation
│   │   ├── a4_monitoring.py         # SLA views & operational monitoring
│   │   ├── a5_smoke_test.py         # End-to-end smoke test runner
│   │   ├── c1_drift_agent.py        # Schema drift detector
│   │   └── c2_proposal_agent.py     # Drift mitigation proposer
│   ├── entity_model.py              # Parent/child XML entity decomposition & ER diagram generator
│   ├── ddl_compiler.py              # Snowflake Snowpipe & Dynamic Table DDL generator
│   ├── xml_infer.py                 # XML parsing, XPath extraction & narrowest type ladder
│   ├── snowflake_client.py          # Snowflake connector (External Browser SSO & simulation)
│   ├── web_app.py                   # Starlette/Uvicorn Control Plane UI backend
│   └── ui/                          # Web UI dashboard with interactive Mermaid ER viewer
├── tests/                           # End-to-end automated unit test suite
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
Run [`snowflake_bootstrap/account_bootstrap.sql`](./snowflake_bootstrap/account_bootstrap.sql) in Snowflake as `ACCOUNTADMIN` to set up:
- Warehouse: `COMPUTE_WH` (with 5-minute auto-suspend)
- Roles: `DATA_ENGINEER_ROLE`, `DATA_STEWARD_ROLE`, `DATA_ANALYST_ROLE`, `DATAHUB_READER_ROLE`
- Database: `ENTERPRISE_DW`
- Schemas: `RAW`, `STAGING`, `CURATED`, and `OPS`

### 3. Launch the Control Plane UI
Start the web dashboard:
```bash
python -m src.web_app
```
Open **[http://localhost:8765](http://localhost:8765)** to:
- Review sample XML schemas.
- Inspect the interactive **Mermaid ER model** showing child entity decomposition and foreign keys.
- Approve 3-Layer YAML schemas before triggering DDL generation.
- Execute A5 smoke tests and deploy live to Snowflake via External Browser SSO.

### 4. Or Use the AI Onboarding Skill
In the chat interface, simply invoke the skill:
```text
/dataset-onboarding
```
The skill will interactively guide you through:
1. Ingesting and inferring sample XMLs.
2. Reviewing the child hierarchy decomposition and ER diagram at the **C3 Schema Approval Gate**.
3. Compiling all Snowpipe and Dynamic Table DDLs.
4. Running the A5 smoke test and reviewing the report before live deployment.
