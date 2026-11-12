# Graph Report - xml_to_snowflake  (2026-11-12)

## Corpus Check
- 158 files · ~139,478 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 53 file(s) not represented in the graph (top: .xml 33, .gz 12, .lkml 6)

## Summary
- 2436 nodes · 3508 edges · 109 communities (88 shown, 21 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 63 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9c2399f8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- type_assertions
- type_assertions
- ClaudeClient
- env
- web_app.py
- snowflake_client.py
- json
- snowflake_live_deployment
- snowflake_live_deployment
- c2_proposal_agent.py
- entities
- type_assertions
- accepted_values
- accepted_values
- models.py
- analytics/snowflake_live_deployment.yaml
- orders/snowflake_live_deployment.yaml
- entities
- fetchState
- snowflake
- entities
- tables
- tables
- tables
- orders/datahub_urns.yaml
- tables
- accepted_values
- tables
- tables
- accepted_values
- accepted_values
- entities
- audit_xml_hierarchical_integrity
- registry/datahub_urns.yaml
- enterprise_orders/datahub_urns.yaml
- tables
- fields
- G3_Business
- fields
- fields
- fields
- tables
- tables
- orchestrator.py
- type_assertions
- DatasetMapping
- Orders Bootstrap Report
- Dataset README — orders
- metrics_collector.py
- analytics/quality_rules.yaml
- benchmark_large_feed.py
- validate-and-test
- enterprise_orders/pipeline_deployment_manifest.yaml
- analytics/pipeline_deployment_manifest.yaml
- orders/pipeline_deployment_manifest.yaml
- TestHierarchicalModel
- xml_infer.py
- A5 Smoke Test Report — analytics
- enterprise_orders/monitoring_config.yaml
- enterprise_orders/onboarding_manifest.yaml
- registry/monitoring_config.yaml
- registry/onboarding_manifest.yaml
- analytics/monitoring_config.yaml
- analytics/onboarding_manifest.yaml
- orders/monitoring_config.yaml
- orders/onboarding_manifest.yaml
- XML to Snowflake UI Control Plane
- A5 Smoke Test Report — orders
- enterprise_orders/provisioned_objects.yaml
- registry/quality_rules.yaml
- analytics/provisioned_objects.yaml
- orders/provisioned_objects.yaml
- ddl_compiler.py
- entity_model.py
- analyze_quality_trends
- test_hierarchical_model.py
- EntityModel
- enterprise_orders/contract.yaml
- Entity
- orders/contract.yaml
- Project Dependencies (requirements.txt)
- XML to Snowflake Agent-Assisted Pipeline
- enterprise_orders/datahub_stub.yaml
- registry/datahub_stub.yaml
- registry/provisioned_objects.yaml
- analytics/datahub_stub.yaml
- orders/datahub_stub.yaml
- Snowflake Account Bootstrap README
- TestDataHubIntegration
- API /api/llm-config
- API /api/snowflake-config
- API /api/export/changelog
- API /api/export/dbt
- API /api/export/openapi
- UI Index HTML
- run_reconciliation_audit
- 📋 Standard Onboarding Workflow
- TestDriftScenarios
- push_to_datahub.py
- TestChildEntityApproval
- test_alert_api.py
- dataset-onboarding.md

## God Nodes (most connected - your core abstractions)
1. `type_assertions` - 158 edges
2. `type_assertions` - 158 edges
3. `DatasetMapping` - 50 edges
4. `type_assertions` - 41 edges
5. `build_entity_model()` - 36 edges
6. `process_runtime_file_with_drift_control()` - 26 edges
7. `run_data_steward_agent()` - 24 edges
8. `run_ddl_generator_agent()` - 23 edges
9. `run_full_onboarding_workflow()` - 23 edges
10. `audit_xml_hierarchical_integrity()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `TestClaudeDataStewardAgent` --uses--> `DataModelSpec`  [INFERRED]
  tests/test_llm_steward.py → src/models.py
- `TestClaudeDataStewardAgent` --uses--> `LayerSchemaYaml`  [INFERRED]
  tests/test_llm_steward.py → src/models.py
- `TestHierarchicalModel` --uses--> `DatasetMapping`  [INFERRED]
  tests/test_hierarchical_model.py → src/models.py
- `run_benchmark()` --uses--> `DatasetMapping`  [INFERRED]
  scripts/benchmark_large_feed.py → src/models.py
- `Step 1: Data Steward & Modeling Agent` --references--> `gold_schema.yaml (Gold Layer)`  [INFERRED]
  src/ui/index.html → registry/orders/bootstrap_report.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Alerts and Notification Flow** — src_ui_index_togglealersdrawer, src_ui_index_loadalerts, src_ui_index_sendtestalert [EXTRACTED 0.95]
- **3-Step Agentic Onboarding Workflow** — concept_data_steward_agent, concept_ddl_generator_agent, concept_e2e_deployment, concept_claude_haiku [EXTRACTED 1.00]
- **3-Layer Medallion Pipeline: RAW → STAGE → GOLD** — table_raw_orders, table_staging_orders, table_curated_orders, concept_snowpipe_ingestion, concept_dynamic_table_refresh [EXTRACTED 1.00]
- **Orders Medallion Pipeline: RAW → STAGING → CURATED** — datasets_orders_raw_table, datasets_orders_staging_table, datasets_orders_curated_table, datasets_orders_quarantine_table [EXTRACTED 1.00]
- **Quality Gate Control Flow: G1, G2, G3, O3 Quarantine** — concept_g1_gate, concept_g2_gate, concept_g3_gate, concept_o3_quarantine [EXTRACTED 1.00]
- **Quality Gate Validation Flow (G1 + G2 + G3)** — concept_gate_g1, concept_gate_g2, concept_gate_g3 [EXTRACTED 1.00]
- **Schema Drift Lifecycle: Additive (AUTO_APPLIED) vs Breaking (PENDING_C3_APPROVAL)** — concept_additive_drift, concept_breaking_drift, datasets_orders_registry_proposals_proposal_020, datasets_orders_registry_proposals_proposal_100 [EXTRACTED 1.00]
- **Runtime Ingest Operations Flow** — src_ui_index_ingestselectedfile, src_ui_index_quickscenario, src_ui_index_runingestcall, src_ui_index_replayquarantine [INFERRED 0.85]
- **Schema Approval Pipeline Flow** — src_ui_index_collectschemaedits, src_ui_index_saveschemaoverrides, src_ui_index_approveyamlsonly, src_ui_index_approveandprovision [INFERRED 0.90]

## Communities (109 total, 21 thin omitted)

### Community 0 - "type_assertions"
Cohesion: 0.01
Nodes (158): type_assertions, /Order/AuditTrail/AuditEvent/ActorId, /Order/AuditTrail/AuditEvent/EventId, /Order/AuditTrail/AuditEvent/EventNotes, /Order/AuditTrail/AuditEvent/EventTimestamp, /Order/AuditTrail/AuditEvent/EventType, /Order/AuditTrail/AuditEvent/@sequence, /Order/@channel (+150 more)

### Community 1 - "type_assertions"
Cohesion: 0.01
Nodes (158): type_assertions, /Order/AuditTrail/AuditEvent/ActorId, /Order/AuditTrail/AuditEvent/EventId, /Order/AuditTrail/AuditEvent/EventNotes, /Order/AuditTrail/AuditEvent/EventTimestamp, /Order/AuditTrail/AuditEvent/EventType, /Order/AuditTrail/AuditEvent/@sequence, /Order/@channel (+150 more)

### Community 2 - "ClaudeClient"
Cohesion: 0.08
Nodes (12): ClaudeClient, _env_bool(), LLMConfig, LLMError, load_llm_config(), main(), _build_prompt(), propose_data_model() (+4 more)

### Community 3 - "env"
Cohesion: 0.05
Nodes (43): default, description, required, environment, if, name, needs, runs-on (+35 more)

### Community 4 - "web_app.py"
Cohesion: 0.08
Nodes (27): generate_samples(), get_snowflake_status(), update_snowflake_config(), api_approve_child_entity(), api_approve_go_live(), api_approve_schema_and_provision(), api_approve_yamls_and_generate_ddl(), api_audit_hierarchy() (+19 more)

### Community 5 - "snowflake_client.py"
Cohesion: 0.10
Nodes (12): audit_live_snowflake(), main(), main(), connect_snowflake_external_browser(), deploy_pipeline_to_snowflake_external_browser(), _exec(), load_snowflake_config(), normalize_snowflake_account() (+4 more)

### Community 6 - "json"
Cohesion: 0.14
Nodes (11): AlertNotification, build_cardinality_alert(), build_drift_alert(), build_reconciliation_alert(), dispatch_alert(), format_pagerduty_payload(), format_slack_blocks(), format_teams_card() (+3 more)

### Community 7 - "snowflake_live_deployment"
Cohesion: 0.04
Nodes (46): active_control_agent, dataset, executed_at, message, query_id, rowcount, sql_preview, status (+38 more)

### Community 8 - "snowflake_live_deployment"
Cohesion: 0.04
Nodes (46): active_control_agent, dataset, executed_at, message, query_id, rowcount, sql_preview, status (+38 more)

### Community 9 - "c2_proposal_agent.py"
Cohesion: 0.09
Nodes (13): run_a1_provision(), _sf_type_to_sqlite(), _bump_version(), handle_drift_findings(), run_ddl_generator_agent(), compile_additive_drift_sql(), compile_gold_dynamic_table_sql(), compile_ops_tables_sql() (+5 more)

### Community 10 - "entities"
Cohesion: 0.05
Nodes (43): attached_contract, column_lineage, curated_column, entity, snowflake_type, staging_column, xpath, datahub_live (+35 more)

### Community 11 - "type_assertions"
Cohesion: 0.04
Nodes (48): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, type_assertions, /ASSETS/@ASOF_DATE (+40 more)

### Community 12 - "accepted_values"
Cohesion: 0.05
Nodes (41): audit_event_sequence, billing_address_address_type, carrier_routing_carrier_code, carrier_routing_service_level, channel, currency_code, customer_customer_tier, customer_kyc_verified (+33 more)

### Community 13 - "accepted_values"
Cohesion: 0.05
Nodes (41): audit_event_sequence, billing_address_address_type, carrier_routing_carrier_code, carrier_routing_service_level, channel, currency_code, customer_customer_tier, customer_kyc_verified (+33 more)

### Community 14 - "models.py"
Cohesion: 0.12
Nodes (19): _apply_llm_proposal(), _build_three_layer_data_model(), data_columns(), fks(), run_data_steward_agent(), ContractSpec, DataModelSpec, EntityRelationship (+11 more)

### Community 15 - "analytics/snowflake_live_deployment.yaml"
Cohesion: 0.05
Nodes (37): authenticator, dataset, deployed, deployed_at, execution_logs, executed_at, message, query_id (+29 more)

### Community 16 - "orders/snowflake_live_deployment.yaml"
Cohesion: 0.05
Nodes (37): authenticator, dataset, deployed, deployed_at, execution_logs, executed_at, message, query_id (+29 more)

### Community 17 - "entities"
Cohesion: 0.05
Nodes (38): business_keys, description, expression, is_business_key, name, nullable, pii_category, semantic_entity (+30 more)

### Community 18 - "fetchState"
Cohesion: 0.07
Nodes (34): API /api/dq/trends, API Endpoint: /api/alerts, API Endpoint: /api/alerts/test, API Endpoint: /api/approve-child-entity, API Endpoint: /api/approve-yamls, API Endpoint: /api/bootstrap, API Endpoint: /api/go-live, API Endpoint: /api/ingest (+26 more)

### Community 19 - "snowflake"
Cohesion: 0.06
Nodes (33): datahub, env, gms_server, mode, platform, ui_url, llm, api_key_env (+25 more)

### Community 20 - "entities"
Cohesion: 0.06
Nodes (33): business_keys, description, expression, is_business_key, name, nullable, pii_category, semantic_entity (+25 more)

### Community 21 - "tables"
Cohesion: 0.06
Nodes (32): description, expression, is_business_key, name, nullable, pii_category, semantic_entity, snowflake_type (+24 more)

### Community 22 - "tables"
Cohesion: 0.06
Nodes (32): description, expression, is_business_key, name, nullable, pii_category, semantic_entity, snowflake_type (+24 more)

### Community 23 - "tables"
Cohesion: 0.06
Nodes (31): description, expression, is_business_key, name, nullable, pii_category, semantic_entity, snowflake_type (+23 more)

### Community 24 - "orders/datahub_urns.yaml"
Cohesion: 0.06
Nodes (31): column_lineage, curated_column, snowflake_type, staging_column, xpath, datahub_live, emitted_at, emitted_urns_count (+23 more)

### Community 25 - "tables"
Cohesion: 0.06
Nodes (31): description, expression, is_business_key, name, nullable, pii_category, semantic_entity, snowflake_type (+23 more)

### Community 26 - "accepted_values"
Cohesion: 0.07
Nodes (29): asof_date, country_classification_set_size, create_date, cusip2_set_size, cusip_alias_set_size, records, dataset, deployed_at (+21 more)

### Community 27 - "tables"
Cohesion: 0.07
Nodes (29): description, expression, is_business_key, name, nullable, pii_category, semantic_entity, snowflake_type (+21 more)

### Community 28 - "tables"
Cohesion: 0.07
Nodes (29): description, expression, is_business_key, name, nullable, pii_category, semantic_entity, snowflake_type (+21 more)

### Community 29 - "accepted_values"
Cohesion: 0.07
Nodes (28): accepted_values, audit_event_sequence, billing_address_address_type, carrier_routing_carrier_code, carrier_routing_service_level, channel, currency_code, customer_customer_tier (+20 more)

### Community 30 - "accepted_values"
Cohesion: 0.07
Nodes (28): accepted_values, audit_event_sequence, billing_address_address_type, carrier_routing_carrier_code, carrier_routing_service_level, channel, currency_code, customer_customer_tier (+20 more)

### Community 31 - "entities"
Cohesion: 0.07
Nodes (27): business_keys, description, expression, is_business_key, name, nullable, snowflake_type, source_xpath (+19 more)

### Community 32 - "audit_xml_hierarchical_integrity"
Cohesion: 0.18
Nodes (3): generate_compliance_certificate(), audit_xml_hierarchical_integrity(), HierarchicalDQFinding

### Community 33 - "registry/datahub_urns.yaml"
Cohesion: 0.07
Nodes (26): attached_contract, column_lineage, curated_column, snowflake_type, staging_column, xpath, dataset, entities (+18 more)

### Community 34 - "enterprise_orders/datahub_urns.yaml"
Cohesion: 0.08
Nodes (25): column_lineage, curated_column, snowflake_type, staging_column, xpath, dataset, entities, adls_landing (+17 more)

### Community 35 - "tables"
Cohesion: 0.08
Nodes (25): description, expression, is_business_key, name, nullable, snowflake_type, source_xpath, dataset (+17 more)

### Community 36 - "fields"
Cohesion: 0.08
Nodes (24): business_keys, dataset, fields, added_in_version, column, confidence, flatten_path, is_array (+16 more)

### Community 37 - "G3_Business"
Cohesion: 0.08
Nodes (24): currency_code, dataset, deployed_at, checks, on_failure, sits_between, on_failure, required_xpaths (+16 more)

### Community 38 - "fields"
Cohesion: 0.08
Nodes (24): business_keys, dataset, fields, added_in_version, column, confidence, flatten_path, is_array (+16 more)

### Community 39 - "fields"
Cohesion: 0.07
Nodes (26): business_keys, dataset, fields, added_in_version, column, confidence, flatten_path, is_array (+18 more)

### Community 40 - "fields"
Cohesion: 0.08
Nodes (24): business_keys, dataset, fields, added_in_version, column, confidence, flatten_path, is_array (+16 more)

### Community 41 - "tables"
Cohesion: 0.08
Nodes (23): description, expression, is_business_key, name, nullable, snowflake_type, source_xpath, dataset (+15 more)

### Community 42 - "tables"
Cohesion: 0.08
Nodes (23): description, expression, is_business_key, name, nullable, snowflake_type, source_xpath, dataset (+15 more)

### Community 43 - "orchestrator.py"
Cohesion: 0.07
Nodes (11): run_a0_intake(), run_a4_monitoring(), ingest_xml_files_into_warehouse(), run_a5_smoke_test(), archive_ingested_file(), approve_c3_go_live(), approve_c3_schema_review(), main() (+3 more)

### Community 44 - "type_assertions"
Cohesion: 0.10
Nodes (20): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, type_assertions, /Order/@currency (+12 more)

### Community 45 - "DatasetMapping"
Cohesion: 0.10
Nodes (11): _emit_to_live_datahub(), _load_datahub_settings(), run_a2_catalog(), detect_new_child_entities(), NewChildEntityProposal, build_entity_model(), DatasetMapping, ColumnDiff (+3 more)

### Community 46 - "Orders Bootstrap Report"
Cohesion: 0.20
Nodes (18): Step 1: Data Steward & Modeling Agent, Step 2: DDL Generator Agent, Dynamic Table Refresh (Snowflake), ENTERPRISE_DW Snowflake Database, G1 Gate: File Arrival, SHA-256 Idempotency, XML Well-Formedness, G2 Gate: Contract — Required XPaths, Type Casts, Row Counts, G3 Gate: Business — Primary Keys, Ranges, Domains, SCD Type 2 MERGE Pattern (+10 more)

### Community 47 - "Dataset README — orders"
Cohesion: 0.13
Nodes (17): Breaking Schema Drift (PENDING_C3_APPROVAL), DataHub URN: curated_orders PROD, DataHub URN: staging_orders PROD, curated_orders (Snowflake SCD2 Table), order_additive_drift.xml, order_breaking_drift.xml, order_malformed.xml, Dataset README — orders (+9 more)

### Community 48 - "metrics_collector.py"
Cohesion: 0.14
Nodes (4): collect_pipeline_metrics(), format_prometheus_metrics(), api_get_metrics(), TestMetricsCollector

### Community 49 - "analytics/quality_rules.yaml"
Cohesion: 0.12
Nodes (16): accepted_values, asof_date, country_classification_set_size, create_date, cusip2_set_size, cusip_alias_set_size, records, dataset (+8 more)

### Community 50 - "benchmark_large_feed.py"
Cohesion: 0.21
Nodes (3): generate_record(), run_benchmark(), generate_synthetic_xml()

### Community 51 - "validate-and-test"
Cohesion: 0.10
Nodes (20): jobs, validate-and-test, python-version, name, on, pull_request, push, branches (+12 more)

### Community 52 - "enterprise_orders/pipeline_deployment_manifest.yaml"
Cohesion: 0.13
Nodes (14): adls_to_raw_mechanism, created_at, dataset, execution_order, generated_by, raw_to_stage_mechanism, sql_artifacts, gold_layer_sql (+6 more)

### Community 53 - "analytics/pipeline_deployment_manifest.yaml"
Cohesion: 0.13
Nodes (14): adls_to_raw_mechanism, created_at, dataset, execution_order, generated_by, raw_to_stage_mechanism, sql_artifacts, gold_layer_sql (+6 more)

### Community 54 - "orders/pipeline_deployment_manifest.yaml"
Cohesion: 0.13
Nodes (14): adls_to_raw_mechanism, created_at, dataset, execution_order, generated_by, raw_to_stage_mechanism, sql_artifacts, gold_layer_sql (+6 more)

### Community 56 - "xml_infer.py"
Cohesion: 0.07
Nodes (20): deploy_a3_quality_gates(), evaluate_file_through_gates(), detect_schema_drift(), DriftFinding, GateCheckResult, QuarantineRecord, TargetTables, build_column_name() (+12 more)

### Community 57 - "A5 Smoke Test Report — analytics"
Cohesion: 0.28
Nodes (13): Additive Schema Drift (AUTO_APPLIED), DataHub URN: curated_analytics PROD, DataHub URN: staging_analytics PROD, Bootstrap Report — analytics, Data Quality & Reconciliation Certificate — ANALYTICS, curated_analytics (DYNAMIC_TABLE 15-min lag), C2 Schema Drift Proposal analytics v0.2.0 (AUTO_APPLIED), C2 Schema Drift Proposal analytics v0.3.0 (AUTO_APPLIED) (+5 more)

### Community 58 - "enterprise_orders/monitoring_config.yaml"
Cohesion: 0.15
Nodes (12): configured_at, dataset, o2_alerts, freshness_sla_hours, quarantine_threshold, routing_source, o4_operator_runbook, first_action (+4 more)

### Community 59 - "enterprise_orders/onboarding_manifest.yaml"
Cohesion: 0.15
Nodes (12): adls_landing_path, created_at, data_steward, dataset, engineering_owner, freshness_sla_hours, onboarding_sample_dir, platform_oncall (+4 more)

### Community 60 - "registry/monitoring_config.yaml"
Cohesion: 0.15
Nodes (12): configured_at, dataset, o2_alerts, freshness_sla_hours, quarantine_threshold, routing_source, o4_operator_runbook, first_action (+4 more)

### Community 61 - "registry/onboarding_manifest.yaml"
Cohesion: 0.15
Nodes (12): adls_landing_path, created_at, data_steward, dataset, engineering_owner, freshness_sla_hours, onboarding_sample_dir, platform_oncall (+4 more)

### Community 62 - "analytics/monitoring_config.yaml"
Cohesion: 0.15
Nodes (12): configured_at, dataset, o2_alerts, freshness_sla_hours, quarantine_threshold, routing_source, o4_operator_runbook, first_action (+4 more)

### Community 63 - "analytics/onboarding_manifest.yaml"
Cohesion: 0.15
Nodes (12): adls_landing_path, created_at, data_steward, dataset, engineering_owner, freshness_sla_hours, onboarding_sample_dir, platform_oncall (+4 more)

### Community 64 - "orders/monitoring_config.yaml"
Cohesion: 0.15
Nodes (12): configured_at, dataset, o2_alerts, freshness_sla_hours, quarantine_threshold, routing_source, o4_operator_runbook, first_action (+4 more)

### Community 65 - "orders/onboarding_manifest.yaml"
Cohesion: 0.15
Nodes (12): adls_landing_path, created_at, data_steward, dataset, engineering_owner, freshness_sla_hours, onboarding_sample_dir, platform_oncall (+4 more)

### Community 66 - "XML to Snowflake UI Control Plane"
Cohesion: 0.21
Nodes (12): Anthropic Claude Haiku LLM Agent, DataHub Catalog & Lineage, Step 3: E2E Deployment & Final Sign-Off, 3-Layer Medallion Architecture (RAW → STAGE → GOLD), O3 Quarantine Table, C1/C2 Schema Drift Control Plane, Snowflake External Browser SSO, Orders Schema Drift Proposal v0.2.0 (+4 more)

### Community 67 - "A5 Smoke Test Report — orders"
Cohesion: 0.27
Nodes (12): G1: File Gate (Arrival, SHA-256, XML well-formedness), G2: Contract Gate (Required XPaths, type casts, row counts), G3: Business Gate (Primary keys, ranges, domains), Bootstrap Report — enterprise_orders, curated_enterprise_orders (DYNAMIC_TABLE 15-min lag), raw_enterprise_orders (RAW NORMAL_TABLE), A5 Smoke Test Report — enterprise_orders, staging_enterprise_orders (DYNAMIC_TABLE 5-min lag) (+4 more)

### Community 68 - "enterprise_orders/provisioned_objects.yaml"
Cohesion: 0.17
Nodes (11): dataset, deployed_by, deployment_manifest, local_warehouse_db, pipeline_topology, adls_to_raw, raw_to_stage, stage_to_gold (+3 more)

### Community 69 - "registry/quality_rules.yaml"
Cohesion: 0.17
Nodes (11): accepted_values, currency_code, dataset, freshness_sla_hours, not_null_columns, numeric_ranges, column, max_value (+3 more)

### Community 70 - "analytics/provisioned_objects.yaml"
Cohesion: 0.17
Nodes (11): dataset, deployed_by, deployment_manifest, local_warehouse_db, pipeline_topology, adls_to_raw, raw_to_stage, stage_to_gold (+3 more)

### Community 71 - "orders/provisioned_objects.yaml"
Cohesion: 0.17
Nodes (11): dataset, deployed_by, deployment_manifest, local_warehouse_db, pipeline_topology, adls_to_raw, raw_to_stage, stage_to_gold (+3 more)

### Community 72 - "ddl_compiler.py"
Cohesion: 0.21
Nodes (8): _column_expr(), compile_staging_dynamic_table_sql(), _flatten_plan(), _levels(), _pk_expr(), _xmlget_chain(), EntityColumn, cast_varchar_expr()

### Community 73 - "entity_model.py"
Cohesion: 0.15
Nodes (8): keep(), nearest_ancestor(), resolve_rep_path(), unique_name(), _entity_name(), _er_type(), _parts(), render_er_diagram()

### Community 75 - "test_hierarchical_model.py"
Cohesion: 0.29
Nodes (3): export_json_schema(), export_openapi_spec(), _map_sf_type_to_json_schema()

### Community 76 - "EntityModel"
Cohesion: 0.20
Nodes (3): EntityModel, export_lookml_project(), _map_sf_to_lookml_type()

### Community 77 - "enterprise_orders/contract.yaml"
Cohesion: 0.25
Nodes (7): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, version

### Community 78 - "Entity"
Cohesion: 0.39
Nodes (4): key_columns(), _fk_comment(), add_column(), Entity

### Community 79 - "orders/contract.yaml"
Cohesion: 0.25
Nodes (7): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, version

### Community 80 - "Project Dependencies (requirements.txt)"
Cohesion: 0.25
Nodes (8): acryl-datahub (>=1.7.0), anthropic (>=0.40.0), Project Dependencies (requirements.txt), pydantic (>=2.0.0), PyYAML (>=6.0), snowflake-connector-python (>=4.0.0,<5.0.0), starlette (>=0.30.0), uvicorn (>=0.20.0)

### Community 81 - "XML to Snowflake Agent-Assisted Pipeline"
Cohesion: 0.29
Nodes (7): account_bootstrap.sql, DDL Compiler (ddl_compiler.py), XML to Snowflake Agent-Assisted Pipeline, requirements.txt, Snowflake Bootstrap Directory, Agents Directory (A0-A5, C0-C2), Web App Control Plane (web_app.py)

### Community 82 - "enterprise_orders/datahub_stub.yaml"
Cohesion: 0.33
Nodes (5): created_at, created_by, owners, status, urn

### Community 83 - "registry/datahub_stub.yaml"
Cohesion: 0.33
Nodes (5): created_at, created_by, owners, status, urn

### Community 84 - "registry/provisioned_objects.yaml"
Cohesion: 0.33
Nodes (5): dataset, local_warehouse_db, provisioned_objects, snowflake_ddl_file, version

### Community 85 - "analytics/datahub_stub.yaml"
Cohesion: 0.33
Nodes (5): created_at, created_by, owners, status, urn

### Community 86 - "orders/datahub_stub.yaml"
Cohesion: 0.33
Nodes (5): created_at, created_by, owners, status, urn

### Community 87 - "Snowflake Account Bootstrap README"
Cohesion: 0.50
Nodes (4): COMPUTE_WH Snowflake Warehouse (XSMALL), Snowflake RBAC Hierarchy, account_bootstrap.sql, Snowflake Account Bootstrap README

### Community 99 - "run_reconciliation_audit"
Cohesion: 0.14
Nodes (4): run_all_pipeline_checks(), emit_analytics_assertions(), ReconciliationReport, run_reconciliation_audit()

### Community 100 - "📋 Standard Onboarding Workflow"
Cohesion: 0.20
Nodes (9): 🏗️ Architecture & Modeling Principles, 🛑 HUMAN APPROVAL GATE 1: C3 Data Model & Schema Review, 🛑 HUMAN APPROVAL GATE 2: C3 Go-Live & Snowflake Deployment, 📋 Standard Onboarding Workflow, Step 1: Intake & Hierarchical Schema Inference (A0 & Step 1 Agent), Step 2: DDL Compilation (Step 2 Agent), Step 3: Local Provisioning & Smoke Testing (A1–A5 Agents), 🔍 Troubleshooting & Special Cases (+1 more)

## Knowledge Gaps
- **64 isolated node(s):** `API Endpoint: /api/alerts`, `API Endpoint: /api/alerts/test`, `API Endpoint: /api/approve-child-entity`, `API Endpoint: /api/approve-yamls`, `API Endpoint: /api/bootstrap` (+59 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1820 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DatasetMapping` connect `DatasetMapping` to `ClaudeClient`, `web_app.py`, `snowflake_client.py`, `ddl_compiler.py`, `c2_proposal_agent.py`, `entity_model.py`, `orchestrator.py`, `test_hierarchical_model.py`, `models.py`, `benchmark_large_feed.py`, `TestHierarchicalModel`, `xml_infer.py`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `DatasetMapping` (e.g. with `run_benchmark()` and `evaluate_file_through_gates()`) actually correct?**
  _`DatasetMapping` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `API Endpoint: /api/alerts`, `API Endpoint: /api/alerts/test`, `API Endpoint: /api/approve-child-entity` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `type_assertions` be split into smaller, more focused modules?**
  _Cohesion score 0.012658227848101266 - nodes in this community are weakly interconnected._
- **Why does `type_assertions` connect `type_assertions` to `orders/contract.yaml`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Should `type_assertions` be split into smaller, more focused modules?**
  _Cohesion score 0.012658227848101266 - nodes in this community are weakly interconnected._
- **Why does `type_assertions` connect `type_assertions` to `enterprise_orders/contract.yaml`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._