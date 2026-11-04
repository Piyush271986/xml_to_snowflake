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
    status: Literal["DRAFT", "BOOTSTRAPPED", "APPROVED", "PROVISIONED", "PUBLISHED"] = "DRAFT"
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
