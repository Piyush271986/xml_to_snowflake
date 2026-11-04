# Snowflake Account Bootstrap & RBAC Setup

This folder contains the global, account-level Snowflake setup scripts. These are executed **once** per Snowflake account (by `ACCOUNTADMIN`) before any dataset pipelines are deployed.

---

## 📄 Contents

* **`account_bootstrap.sql`**:
  * **RBAC Hierarchy:**
    * `DATA_ENGINEER_ROLE`: Pipeline operations, tasks, stages, and DDL execution.
    * `DATA_STEWARD_ROLE`: Schema reviews, data quality governance, and quarantine management.
    * `DATA_ANALYST_ROLE`: Read-only access to published curated datasets (`CURATED`) and analytical views.
    * `DATAHUB_READER_ROLE`: Service role for automated DataHub catalog crawling and query lineage.
  * **Warehouse:**
    * `COMPUTE_WH` (`XSMALL`) with `AUTO_SUSPEND = 300` (5 minutes of inactivity).
  * **Database & Schemas:**
    * Database: `ENTERPRISE_DW`
    * Schemas: `RAW`, `STAGING`, `CURATED`, `OPS`.
  * **Automated Future Grants:**
    * Ensures future tables, streams, and tasks created by pipeline agents inherit permissions automatically.

---

## 🚀 Execution Instructions

1. Open your **Snowflake Web UI** (Worksheets).
2. Ensure you are using the role **`ACCOUNTADMIN`**.
3. Open or paste [`account_bootstrap.sql`](./account_bootstrap.sql).
4. Run all statements.
