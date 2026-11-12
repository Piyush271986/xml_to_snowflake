"""Data models for the XML-to-Snowflake schema registry, quality gates, and drift control."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class OnboardingManifest(BaseModel):
    dataset: str
    source_system: str
    adls_landing_path: str
    onboarding_sample_dir: str
    data_steward: str
    engineering_owner: str
    platform_oncall: str = "platform-oncall@enterprise.io"
    freshness_sla_hours: int = 24
    valid_sample_files: list[str] = Field(default_factory=list)
    quarantined_sample_files: list[str] = Field(default_factory=list)
    status: Literal[
        "DRAFT",
        "BOOTSTRAPPED",
        "PENDING_HUMAN_APPROVAL",
        "APPROVED",
        "DDL_GENERATED",
        "PROVISIONED",
        "PUBLISHED",
    ] = "DRAFT"
    created_at: str


PiiCategory = Literal["NONE", "CONTACT", "FINANCIAL", "GOVERNMENT_ID", "LOCATION", "OTHER"]


class LayerColumnSpec(BaseModel):
    name: str
    snowflake_type: str
    nullable: bool = True
    source_xpath: str | None = None
    expression: str | None = None
    description: str | None = None
    is_business_key: bool = False
    semantic_entity: str | None = None
    pii_category: PiiCategory | None = None
    suggested_name: str | None = None


class LLMColumnAnnotation(BaseModel):
    """Claude's per-column annotation. Suggestions only — never auto-renames executable columns."""
    column: str
    description: str
    semantic_entity: str
    pii_category: PiiCategory = "NONE"
    suggested_name: str | None = None


class LLMGoldEntity(BaseModel):
    """A Gold-layer dimensional entity proposed by Claude for human review."""
    name: str
    entity_type: Literal["FACT", "DIMENSION", "BRIDGE", "SATELLITE"]
    grain: str
    primary_keys: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    rationale: str = ""


class LLMModelingProposal(BaseModel):
    model: str
    summary: str
    column_annotations: list[LLMColumnAnnotation] = Field(default_factory=list)
    gold_entities: list[LLMGoldEntity] = Field(default_factory=list)
    steward_review_notes: list[str] = Field(default_factory=list)


class ForeignKeySpec(BaseModel):
    """Logical foreign key from a child entity table to its parent entity table (Dynamic Tables cannot enforce constraints)."""
    column: str
    references_table: str
    references_column: str


class LayerTableSpec(BaseModel):
    table_name: str
    entity: str | None = None
    parent_table: str | None = None
    foreign_keys: list[ForeignKeySpec] = Field(default_factory=list)
    layer: Literal["RAW", "STAGE", "GOLD"]
    table_type: Literal["NORMAL_TABLE", "DYNAMIC_TABLE"]
    ingestion_or_refresh: Literal["SNOWPIPE", "DYNAMIC_TABLE_REFRESH"]
    upstream_source: str
    target_lag: str | None = None
    warehouse: str | None = None
    grain: str
    primary_keys: list[str] = Field(default_factory=list)
    flatten_path: str | None = None
    columns: list[LayerColumnSpec] = Field(default_factory=list)


class LayerSchemaYaml(BaseModel):
    dataset: str
    version: str = "0.1.0"
    layer: Literal["RAW", "STAGE", "GOLD"]
    table_type: Literal["NORMAL_TABLE", "DYNAMIC_TABLE"]
    tables: list[LayerTableSpec] = Field(default_factory=list)
    generated_by: str = "step1_data_steward_agent"
    ddl_generated: bool = False


class EntityRelationship(BaseModel):
    parent_entity: str
    child_entity: str
    relationship_type: Literal["1:1", "1:N"]
    join_keys: list[str]
    source_xpath: str
    kind: Literal["LINEAGE", "FOREIGN_KEY"] = "LINEAGE"
    layer: str | None = None
    fk_column: str | None = None
    parent_pk_column: str | None = None


class DataModelSpec(BaseModel):
    dataset: str
    version: str = "0.1.0"
    modeling_strategy: str = "Medallion 3-Layer (RAW Normal Table -> STAGE Dynamic Table -> GOLD Dynamic Table)"
    root_element: str
    record_element: str | None = None
    top_level_fields: list[str] = Field(default_factory=list)
    business_keys: list[str]
    raw_layer_file: str = "raw_schema.yaml"
    staging_layer_file: str = "staging_schema.yaml"
    gold_layer_file: str = "gold_schema.yaml"
    entities: list[LayerTableSpec] = Field(default_factory=list)
    relationships: list[EntityRelationship] = Field(default_factory=list)
    approval_status: Literal["PENDING_HUMAN_APPROVAL", "APPROVED", "REJECTED"] = "PENDING_HUMAN_APPROVAL"
    modeling_engine: Literal["rule_based", "anthropic_claude"] = "rule_based"
    llm_model: str | None = None
    llm_note: str | None = None
    llm_proposal: LLMModelingProposal | None = None
    er_diagram_staging: str = ""
    er_diagram_curated: str = ""


class PipelineDeploymentManifest(BaseModel):
    dataset: str
    version: str
    generated_by: str = "step2_ddl_generator_agent"
    adls_to_raw_mechanism: str = "SNOWPIPE"
    raw_to_stage_mechanism: str = "DYNAMIC_TABLE"
    stage_to_gold_mechanism: str = "DYNAMIC_TABLE"
    sql_artifacts: dict[str, str] = Field(default_factory=dict)
    execution_order: list[str] = Field(default_factory=list)
    created_at: str


class FieldMapping(BaseModel):
    xpath: str
    column: str
    snowflake_type: str
    xml_expr: str
    required: bool
    is_array: bool = False
    flatten_path: str | None = None
    is_attribute: bool = False
    confidence: float
    sample_values: list[str] = Field(default_factory=list)
    origin: Literal["c0_bootstrap", "c1_drift_additive", "c3_steward_override"] = "c0_bootstrap"
    added_in_version: str = "0.1.0"


class TargetTables(BaseModel):
    raw_table: str
    staging_table: str
    curated_table: str
    quarantine_table: str
    dq_results_table: str


class DatasetMapping(BaseModel):
    dataset: str
    version: str = "0.1.0"
    source: str = "sample_inference"
    root_element: str
    record_element: str | None = None
    top_level_fields: list[str] = Field(default_factory=list)
    business_keys: list[str]
    targets: TargetTables
    fields: list[FieldMapping]


class ContractSpec(BaseModel):
    dataset: str
    version: str
    root_element: str
    required_xpaths: list[str]
    type_assertions: dict[str, str]
    expected_rows_per_file_min: int
    expected_rows_per_file_max: int
    allow_unknown_elements: bool = True  # Unknown elements trigger C1 Drift Agent


class RangeRule(BaseModel):
    column: str
    min_value: float | None = None
    max_value: float | None = None


class QualityRulesSpec(BaseModel):
    dataset: str
    version: str
    primary_keys: list[str]
    not_null_columns: list[str]
    accepted_values: dict[str, list[str]] = Field(default_factory=dict)
    numeric_ranges: list[RangeRule] = Field(default_factory=list)
    freshness_sla_hours: int = 24


class QuarantineRecord(BaseModel):
    dataset: str
    file_name: str
    file_sha256: str
    gate_id: Literal["G1", "G2", "G3"]
    failure_reason: str
    raw_payload: str
    quarantined_at: str
    replayed: bool = False


class GateCheckResult(BaseModel):
    dataset: str
    file_name: str
    gate_id: Literal["G1", "G2", "G3"]
    check_name: str
    passed: bool
    details: str
    checked_at: str


class DriftFinding(BaseModel):
    xpath: str
    change_type: Literal["NEW_OPTIONAL_ELEMENT", "MISSING_REQUIRED_ELEMENT", "TYPE_INCOMPATIBLE"]
    classification: Literal["ADDITIVE", "BREAKING"]
    observed_type: str | None = None
    expected_type: str | None = None
    sample_value: str | None = None
    source_file: str


class DriftProposal(BaseModel):
    dataset: str
    current_version: str
    proposed_version: str
    status: Literal["AUTO_APPLIED", "PENDING_C3_APPROVAL", "APPROVED", "REJECTED"]
    additive_findings: list[DriftFinding] = Field(default_factory=list)
    breaking_findings: list[DriftFinding] = Field(default_factory=list)
    proposed_sql: list[str] = Field(default_factory=list)
    downstream_impact: list[str] = Field(default_factory=list)
    created_at: str
