# Graph Report - xml_to_snowflake  (2026-11-11)

## Corpus Check
- 164 files · ~138,817 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 49 file(s) not represented in the graph (top: .xml 33, .gz 8, .lkml 6)

## Summary
- 2385 nodes · 3484 edges · 106 communities (86 shown, 20 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 106 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9917f629`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- type_assertions
- type_assertions
- c0_bootstrap.py
- c2_proposal_agent.py
- Request
- snowflake_client.py
- json
- snowflake_live_deployment
- snowflake_live_deployment
- models.py
- entities
- type_assertions
- accepted_values
- accepted_values
- entity_model.py
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
- DatasetMapping
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
- run_full_onboarding_workflow
- type_assertions
- TestHierarchicalModel
- Orders Bootstrap Report
- Dataset README — orders
- format_prometheus_metrics
- analytics/quality_rules.yaml
- sources
- TestDataHubIntegration
- enterprise_orders/pipeline_deployment_manifest.yaml
- analytics/pipeline_deployment_manifest.yaml
- orders/pipeline_deployment_manifest.yaml
- pathlib
- benchmark_large_feed.py
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
- EntityModel
- web_app.py
- test_llm_steward.py
- lookml_exporter.py
- enterprise_orders/contract.yaml
- analytics/contract.yaml
- orders/contract.yaml
- Project Dependencies (requirements.txt)
- XML to Snowflake Agent-Assisted Pipeline
- enterprise_orders/datahub_stub.yaml
- registry/datahub_stub.yaml
- registry/provisioned_objects.yaml
- analytics/datahub_stub.yaml
- orders/datahub_stub.yaml
- Snowflake Account Bootstrap README
- TestChildEntityApproval
- API /api/llm-config
- API /api/snowflake-config
- API /api/export/changelog
- API /api/export/dbt
- API /api/export/openapi
- UI Index HTML
- datetime
- 📋 Standard Onboarding Workflow
- export_dbt_project
- build_entity_model
- render_er_diagram
- TestAlertAPI
- TestDqTrends

## God Nodes (most connected - your core abstractions)
1. `type_assertions` - 158 edges
2. `type_assertions` - 158 edges
3. `DatasetMapping` - 64 edges
4. `type_assertions` - 43 edges
5. `build_entity_model()` - 37 edges
6. `process_runtime_file_with_drift_control()` - 26 edges
7. `run_data_steward_agent()` - 24 edges
8. `run_ddl_generator_agent()` - 23 edges
9. `run_full_onboarding_workflow()` - 23 edges
10. `audit_xml_hierarchical_integrity()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `run_benchmark()` --uses--> `DatasetMapping`  [INFERRED]
  scripts/benchmark_large_feed.py → src/models.py
- `TestHierarchicalModel` --uses--> `DatasetMapping`  [INFERRED]
  tests/test_hierarchical_model.py → src/models.py
- `TestXmlToSnowflakePipeline` --uses--> `DatasetMapping`  [INFERRED]
  tests/test_pipeline_e2e.py → src/models.py
- `Step 1: Data Steward & Modeling Agent` --references--> `gold_schema.yaml (Gold Layer)`  [INFERRED]
  src/ui/index.html → registry/orders/bootstrap_report.md
- `Step 1: Data Steward & Modeling Agent` --references--> `raw_schema.yaml (RAW Layer)`  [INFERRED]
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

## Communities (106 total, 20 thin omitted)

### Community 0 - "type_assertions"
Cohesion: 0.01
Nodes (158): type_assertions, /Order/AuditTrail/AuditEvent/ActorId, /Order/AuditTrail/AuditEvent/EventId, /Order/AuditTrail/AuditEvent/EventNotes, /Order/AuditTrail/AuditEvent/EventTimestamp, /Order/AuditTrail/AuditEvent/EventType, /Order/AuditTrail/AuditEvent/@sequence, /Order/@channel (+150 more)

### Community 1 - "type_assertions"
Cohesion: 0.01
Nodes (158): type_assertions, /Order/AuditTrail/AuditEvent/ActorId, /Order/AuditTrail/AuditEvent/EventId, /Order/AuditTrail/AuditEvent/EventNotes, /Order/AuditTrail/AuditEvent/EventTimestamp, /Order/AuditTrail/AuditEvent/EventType, /Order/AuditTrail/AuditEvent/@sequence, /Order/@channel (+150 more)

### Community 2 - "c0_bootstrap.py"
Cohesion: 0.06
Nodes (28): _apply_llm_proposal(), _build_three_layer_data_model(), data_columns(), fks(), key_columns(), run_data_steward_agent(), ClaudeClient, _env_bool() (+20 more)

### Community 3 - "c2_proposal_agent.py"
Cohesion: 0.09
Nodes (14): run_a1_provision(), _sf_type_to_sqlite(), _bump_version(), handle_drift_findings(), run_ddl_generator_agent(), compile_additive_drift_sql(), compile_ops_tables_sql(), compile_raw_snowpipe_sql() (+6 more)

### Community 4 - "Request"
Cohesion: 0.13
Nodes (17): api_approve_child_entity(), api_audit_hierarchy(), api_configure_llm(), api_export_changelog(), api_export_dq_certificate(), api_get_alerts(), api_get_dq_trends(), api_ingest_xml() (+9 more)

### Community 5 - "snowflake_client.py"
Cohesion: 0.11
Nodes (14): audit_live_snowflake(), connect_snowflake_external_browser(), deploy_pipeline_to_snowflake_external_browser(), _exec(), get_snowflake_status(), load_snowflake_config(), normalize_snowflake_account(), SnowflakeConnectionConfig (+6 more)

### Community 6 - "json"
Cohesion: 0.16
Nodes (10): AlertNotification, build_cardinality_alert(), build_drift_alert(), build_reconciliation_alert(), dispatch_alert(), format_pagerduty_payload(), format_slack_blocks(), format_teams_card() (+2 more)

### Community 7 - "snowflake_live_deployment"
Cohesion: 0.04
Nodes (46): active_control_agent, dataset, executed_at, message, query_id, rowcount, sql_preview, status (+38 more)

### Community 8 - "snowflake_live_deployment"
Cohesion: 0.04
Nodes (46): active_control_agent, dataset, executed_at, message, query_id, rowcount, sql_preview, status (+38 more)

### Community 9 - "models.py"
Cohesion: 0.16
Nodes (10): deploy_a3_quality_gates(), evaluate_file_through_gates(), ingest_xml_files_into_warehouse(), run_a5_smoke_test(), ContractSpec, GateCheckResult, QualityRulesSpec, QuarantineRecord (+2 more)

### Community 10 - "entities"
Cohesion: 0.05
Nodes (43): attached_contract, column_lineage, curated_column, entity, snowflake_type, staging_column, xpath, datahub_live (+35 more)

### Community 11 - "type_assertions"
Cohesion: 0.05
Nodes (43): type_assertions, /ASSETS/@ASOF_DATE, /ASSETS/ASSET/BND_CORP/ACCRUAL_DT, /ASSETS/ASSET/BND_CORP/AMT_ISU, /ASSETS/ASSET/BND_CORP/ANNOUNCE_DT, /ASSETS/ASSET/BND_CORP/CALC_TYPE, /ASSETS/ASSET/BND_CORP/CALL_MANDATORY, /ASSETS/ASSET/BND_CORP/CALL_TYPE (+35 more)

### Community 12 - "accepted_values"
Cohesion: 0.05
Nodes (41): audit_event_sequence, billing_address_address_type, carrier_routing_carrier_code, carrier_routing_service_level, channel, currency_code, customer_customer_tier, customer_kyc_verified (+33 more)

### Community 13 - "accepted_values"
Cohesion: 0.05
Nodes (41): audit_event_sequence, billing_address_address_type, carrier_routing_carrier_code, carrier_routing_service_level, channel, currency_code, customer_customer_tier, customer_kyc_verified (+33 more)

### Community 14 - "entity_model.py"
Cohesion: 0.10
Nodes (10): run_dbt_style_assertions(), _entity_name(), _er_type(), TargetTables, flatten_xml_to_rows(), infer_schema_from_xml_files(), walk(), infer_single_value_type() (+2 more)

### Community 15 - "analytics/snowflake_live_deployment.yaml"
Cohesion: 0.05
Nodes (37): authenticator, dataset, deployed, deployed_at, execution_logs, executed_at, message, query_id (+29 more)

### Community 16 - "orders/snowflake_live_deployment.yaml"
Cohesion: 0.05
Nodes (37): authenticator, dataset, deployed, deployed_at, execution_logs, executed_at, message, query_id (+29 more)

### Community 17 - "entities"
Cohesion: 0.05
Nodes (36): business_keys, description, expression, is_business_key, name, nullable, pii_category, semantic_entity (+28 more)

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

### Community 32 - "DatasetMapping"
Cohesion: 0.11
Nodes (11): detect_schema_drift(), detect_new_child_entities(), NewChildEntityProposal, DatasetMapping, DriftFinding, main(), process_runtime_file_with_drift_control(), extract_xml_xpaths_and_values() (+3 more)

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
Cohesion: 0.08
Nodes (24): business_keys, dataset, fields, added_in_version, column, confidence, flatten_path, is_array (+16 more)

### Community 40 - "fields"
Cohesion: 0.08
Nodes (24): business_keys, dataset, fields, added_in_version, column, confidence, flatten_path, is_array (+16 more)

### Community 41 - "tables"
Cohesion: 0.08
Nodes (23): description, expression, is_business_key, name, nullable, snowflake_type, source_xpath, dataset (+15 more)

### Community 42 - "tables"
Cohesion: 0.08
Nodes (23): description, expression, is_business_key, name, nullable, snowflake_type, source_xpath, dataset (+15 more)

### Community 43 - "run_full_onboarding_workflow"
Cohesion: 0.07
Nodes (11): _emit_to_live_datahub(), _load_datahub_settings(), run_a2_catalog(), run_a4_monitoring(), OnboardingManifest, approve_c3_go_live(), approve_c3_schema_review(), run_full_onboarding_workflow() (+3 more)

### Community 44 - "type_assertions"
Cohesion: 0.10
Nodes (20): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, type_assertions, /Order/@currency (+12 more)

### Community 46 - "Orders Bootstrap Report"
Cohesion: 0.20
Nodes (18): Step 1: Data Steward & Modeling Agent, Step 2: DDL Generator Agent, Dynamic Table Refresh (Snowflake), ENTERPRISE_DW Snowflake Database, G1 Gate: File Arrival, SHA-256 Idempotency, XML Well-Formedness, G2 Gate: Contract — Required XPaths, Type Casts, Row Counts, G3 Gate: Business — Primary Keys, Ranges, Domains, SCD Type 2 MERGE Pattern (+10 more)

### Community 47 - "Dataset README — orders"
Cohesion: 0.13
Nodes (17): Breaking Schema Drift (PENDING_C3_APPROVAL), DataHub URN: curated_orders PROD, DataHub URN: staging_orders PROD, curated_orders (Snowflake SCD2 Table), order_additive_drift.xml, order_breaking_drift.xml, order_malformed.xml, Dataset README — orders (+9 more)

### Community 48 - "format_prometheus_metrics"
Cohesion: 0.17
Nodes (3): format_prometheus_metrics(), api_get_metrics(), TestMetricsCollector

### Community 49 - "analytics/quality_rules.yaml"
Cohesion: 0.12
Nodes (16): accepted_values, asof_date, country_classification_set_size, create_date, cusip2_set_size, cusip_alias_set_size, records, dataset (+8 more)

### Community 50 - "sources"
Cohesion: 0.12
Nodes (15): description, name, tests, models, columns, description, name, sources (+7 more)

### Community 52 - "enterprise_orders/pipeline_deployment_manifest.yaml"
Cohesion: 0.13
Nodes (14): adls_to_raw_mechanism, created_at, dataset, execution_order, generated_by, raw_to_stage_mechanism, sql_artifacts, gold_layer_sql (+6 more)

### Community 53 - "analytics/pipeline_deployment_manifest.yaml"
Cohesion: 0.13
Nodes (14): adls_to_raw_mechanism, created_at, dataset, execution_order, generated_by, raw_to_stage_mechanism, sql_artifacts, gold_layer_sql (+6 more)

### Community 54 - "orders/pipeline_deployment_manifest.yaml"
Cohesion: 0.13
Nodes (14): adls_to_raw_mechanism, created_at, dataset, execution_order, generated_by, raw_to_stage_mechanism, sql_artifacts, gold_layer_sql (+6 more)

### Community 55 - "pathlib"
Cohesion: 0.07
Nodes (13): run_all_pipeline_checks(), generate_compliance_certificate(), emit_analytics_assertions(), audit_xml_hierarchical_integrity(), HierarchicalDQFinding, map_type_to_datahub(), push_orders_to_datahub(), ReconciliationReport (+5 more)

### Community 56 - "benchmark_large_feed.py"
Cohesion: 0.19
Nodes (4): generate_record(), run_benchmark(), generate_synthetic_xml(), main()

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
Cohesion: 0.15
Nodes (12): _column_expr(), compile_gold_dynamic_table_sql(), compile_staging_dynamic_table_sql(), _fk_comment(), _flatten_plan(), _levels(), _pk_expr(), _xmlget_chain() (+4 more)

### Community 73 - "EntityModel"
Cohesion: 0.21
Nodes (6): EntityModel, export_json_schema(), export_openapi_spec(), _map_sf_type_to_json_schema(), api_export_json_schema(), api_export_openapi()

### Community 75 - "test_llm_steward.py"
Cohesion: 0.17
Nodes (3): run_a0_intake(), generate_samples(), api_bootstrap()

### Community 77 - "enterprise_orders/contract.yaml"
Cohesion: 0.25
Nodes (7): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, version

### Community 78 - "analytics/contract.yaml"
Cohesion: 0.25
Nodes (7): allow_unknown_elements, dataset, expected_rows_per_file_max, expected_rows_per_file_min, required_xpaths, root_element, version

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

### Community 100 - "📋 Standard Onboarding Workflow"
Cohesion: 0.20
Nodes (9): 🏗️ Architecture & Modeling Principles, 🛑 HUMAN APPROVAL GATE 1: C3 Data Model & Schema Review, 🛑 HUMAN APPROVAL GATE 2: C3 Go-Live & Snowflake Deployment, 📋 Standard Onboarding Workflow, Step 1: Intake & Hierarchical Schema Inference (A0 & Step 1 Agent), Step 2: DDL Compilation (Step 2 Agent), Step 3: Local Provisioning & Smoke Testing (A1–A5 Agents), 🔍 Troubleshooting & Special Cases (+1 more)

### Community 102 - "build_entity_model"
Cohesion: 0.47
Nodes (5): build_entity_model(), keep(), nearest_ancestor(), unique_name(), _parts()

## Knowledge Gaps
- **64 isolated node(s):** `API Endpoint: /api/alerts`, `API Endpoint: /api/alerts/test`, `API Endpoint: /api/approve-child-entity`, `API Endpoint: /api/approve-yamls`, `API Endpoint: /api/bootstrap` (+59 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1788 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DatasetMapping` connect `DatasetMapping` to `c0_bootstrap.py`, `c2_proposal_agent.py`, `datetime`, `snowflake_client.py`, `build_entity_model`, `Request`, `ddl_compiler.py`, `models.py`, `web_app.py`, `run_full_onboarding_workflow`, `export_dbt_project`, `EntityModel`, `entity_model.py`, `TestHierarchicalModel`, `pathlib`, `benchmark_large_feed.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `DatasetMapping` (e.g. with `run_benchmark()` and `run_a1_provision()`) actually correct?**
  _`DatasetMapping` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `API Endpoint: /api/alerts`, `API Endpoint: /api/alerts/test`, `API Endpoint: /api/approve-child-entity` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `type_assertions` be split into smaller, more focused modules?**
  _Cohesion score 0.012658227848101266 - nodes in this community are weakly interconnected._
- **Why does `build_entity_model()` connect `build_entity_model` to `DatasetMapping`, `c0_bootstrap.py`, `c2_proposal_agent.py`, `Request`, `snowflake_client.py`, `export_dbt_project`, `ddl_compiler.py`, `EntityModel`, `web_app.py`, `run_full_onboarding_workflow`, `TestHierarchicalModel`, `entity_model.py`, `pathlib`, `benchmark_large_feed.py`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Should `type_assertions` be split into smaller, more focused modules?**
  _Cohesion score 0.012658227848101266 - nodes in this community are weakly interconnected._
- **Why does `TestHierarchicalModel` connect `TestHierarchicalModel` to `DatasetMapping`, `export_dbt_project`, `render_er_diagram`, `lookml_exporter.py`, `pathlib`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._