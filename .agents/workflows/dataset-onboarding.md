---
name: dataset-onboarding
description: Standardized runbook to onboard new XML datasets into Snowflake Medallion Data Lakehouse (RAW -> STAGING Dynamic Tables -> CURATED SCD2 Dynamic Tables)
---

# Workflow: dataset-onboarding

Follow the runbook and procedures in the `dataset-onboarding` skill:

1. **Intake & Schema Inference (Step 1)**:
   - Identify dataset sample XML files.
   - Run intake script / steward agent to produce schemas in `registry/<dataset>/`.
2. **Approval Gate 1**:
   - Present Mermaid ER diagram, PK/FK mappings, and YAML schemas for user review.
   - Do NOT proceed without user approval.
3. **DDL Generation (Step 2)**:
   - Generate Snowpipe, Dynamic Tables (relational flattening), and SCD Type 2 tables in `sql/`.
4. **Provision & Smoke Test (Step 3)**:
   - Run local validation (G1, G2, G3 gates).
5. **Approval Gate 2**:
   - Present smoke test report with zero quarantine errors.
   - Await user confirmation before live Snowflake deployment.

