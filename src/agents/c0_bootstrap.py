"""Step 1 — Data Steward & Modeling Agent (formerly C0 Schema Bootstrap Agent).

Responsibilities:
1. Reads incoming XML sample schemas and creates the RAW layer table schema in YAML format (`raw_schema.yaml`) — NO DDL generated at this step.
2. Performs data modeling for the Staging and Final Gold layers (modeled as Snowflake Dynamic Tables) and generates:
   - `staging_schema.yaml` (Dynamic Table specification)
   - `gold_schema.yaml` (Dynamic Table specification)
   - `data_model.yaml` (End-to-end 3-layer data model & entity relationships)
   - `mapping.yaml`, `contract.yaml`, `quality_rules.yaml`
3. Sends the data model and 3-layer YAML schemas for Human Approval (C3 Gate) before any DDL is generated.
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from src.llm.anthropic_client import ClaudeClient, LLMError, load_llm_config
from src.llm.steward_modeler import propose_data_model
from src.ddl_compiler import _column_expr
from src.entity_model import Entity, build_entity_model, render_er_diagram
from src.models import (
    ContractSpec,
    DataModelSpec,
    DatasetMapping,
    EntityRelationship,
    ForeignKeySpec,
    LayerColumnSpec,
    LayerSchemaYaml,
    LayerTableSpec,
    LLMModelingProposal,
    OnboardingManifest,
    QualityRulesSpec,
    RangeRule,
)
from src.xml_infer import flatten_xml_to_rows, infer_schema_from_xml_files

logger = logging.getLogger(__name__)


def _apply_llm_proposal(
    proposal: LLMModelingProposal,
    schemas: list[LayerSchemaYaml],
    data_model: DataModelSpec,
    mapping: DatasetMapping | None = None,
) -> None:
    """Attach Claude's column annotations to the Stage/Gold YAML columns and record the proposal on the data model."""
    by_col = {a.column: a for a in proposal.column_annotations}
    if mapping is not None:
        # Entity tables may rename columns (e.g. strip the element prefix), so also resolve annotations by XPath
        by_xpath = {f.xpath: by_col[f.column] for f in mapping.fields if f.column in by_col}
    else:
        by_xpath = {}
    for schema in schemas:
        for table in schema.tables:
            for col in table.columns:
                ann = by_xpath.get(col.source_xpath or "") or by_col.get(col.name)
                if ann is None:
                    continue
                col.description = ann.description
                col.semantic_entity = ann.semantic_entity
                col.pii_category = ann.pii_category
                col.suggested_name = ann.suggested_name
    for entity in data_model.entities:
        for col in entity.columns:
            ann = by_xpath.get(col.source_xpath or "") or by_col.get(col.name)
            if ann is not None:
                col.description = ann.description
                col.semantic_entity = ann.semantic_entity
                col.pii_category = ann.pii_category
                col.suggested_name = ann.suggested_name
    data_model.modeling_engine = "anthropic_claude"
    data_model.llm_model = proposal.model
    data_model.llm_proposal = proposal


def _build_three_layer_data_model(
    mapping: DatasetMapping,
) -> tuple[LayerSchemaYaml, LayerSchemaYaml, LayerSchemaYaml, DataModelSpec]:
    """Construct the 3-layer YAML schemas (RAW Normal Table, STAGE Dynamic Table, GOLD Dynamic Table) and DataModelSpec."""
    ds = mapping.dataset

    # 1. RAW Layer Schema (Normal Table loaded via Snowpipe)
    raw_table_spec = LayerTableSpec(
        table_name=mapping.targets.raw_table,
        layer="RAW",
        table_type="NORMAL_TABLE",
        ingestion_or_refresh="SNOWPIPE",
        upstream_source=f"@RAW.ADLS_XML_STAGE/{ds}/",
        target_lag=None,
        warehouse="COMPUTE_WH",
        grain="One row per ingested XML file from ADLS",
        primary_keys=["_file_name", "_file_sha256"],
        flatten_path=None,
        columns=[
            LayerColumnSpec(
                name="_file_name",
                snowflake_type="VARCHAR(512)",
                nullable=False,
                description="Source XML filename in ADLS landing zone",
                is_business_key=True,
            ),
            LayerColumnSpec(
                name="_file_sha256",
                snowflake_type="VARCHAR(64)",
                nullable=False,
                description="SHA-256 content hash for idempotent ingestion",
                is_business_key=True,
            ),
            LayerColumnSpec(
                name="_source_system",
                snowflake_type="VARCHAR(128)",
                nullable=False,
                description="Source ERP / upstream system identifier",
            ),
            LayerColumnSpec(
                name="_load_ts",
                snowflake_type="TIMESTAMP_NTZ",
                nullable=False,
                description="Snowpipe ingestion timestamp",
            ),
            LayerColumnSpec(
                name="raw_xml",
                snowflake_type="VARIANT",
                nullable=False,
                source_xpath=mapping.root_element,
                description="Immutable raw XML payload stored as Snowflake VARIANT",
            ),
        ],
    )
    raw_schema = LayerSchemaYaml(
        dataset=ds,
        version=mapping.version,
        layer="RAW",
        table_type="NORMAL_TABLE",
        tables=[raw_table_spec],
        generated_by="step1_data_steward_agent",
        ddl_generated=False,
    )

    # 2 + 3. STAGE and GOLD layers: ONE Dynamic Table per XML entity (parent + each child hierarchy),
    # children linked to their parent through a deterministic FK (`<parent>_fk` -> `<parent>_pk`)
    model = build_entity_model(mapping)
    sys_stage = [
        LayerColumnSpec(name="_file_name", snowflake_type="VARCHAR(512)", nullable=False),
        LayerColumnSpec(name="_file_sha256", snowflake_type="VARCHAR(64)", nullable=False),
        LayerColumnSpec(name="_staged_ts", snowflake_type="TIMESTAMP_NTZ", nullable=False),
    ]

    def key_columns(ent: Entity) -> list[LayerColumnSpec]:
        cols = [
            LayerColumnSpec(
                name=ent.pk_column,
                snowflake_type="VARCHAR(32)",
                nullable=False,
                is_business_key=False,
                description=f"Surrogate primary key of {ent.name} (MD5 of file identity + element position)",
            )
        ]
        if ent.parent is not None:
            cols.append(
                LayerColumnSpec(
                    name=ent.fk_column or "",
                    snowflake_type="VARCHAR(32)",
                    nullable=False,
                    description=f"Foreign key to {ent.parent.name}.{ent.parent.pk_column}",
                )
            )
        return cols

    def data_columns(ent: Entity, with_expression: bool) -> list[LayerColumnSpec]:
        return [
            LayerColumnSpec(
                name=c.name,
                snowflake_type=c.field.snowflake_type,
                nullable=not (c.field.required and c.name in ent.business_keys),
                source_xpath=c.field.xpath,
                expression=_column_expr(ent, c) if with_expression else c.name,
                is_business_key=c.name in ent.business_keys,
            )
            for c in ent.columns
        ]

    def fks(ent: Entity, parent_table: str | None) -> list[ForeignKeySpec]:
        if ent.parent is None or parent_table is None:
            return []
        return [
            ForeignKeySpec(
                column=ent.fk_column or "",
                references_table=parent_table,
                references_column=ent.parent.pk_column,
            )
        ]

    stage_tables: list[LayerTableSpec] = []
    gold_tables: list[LayerTableSpec] = []
    relationships: list[EntityRelationship] = [
        EntityRelationship(
            parent_entity=mapping.targets.raw_table,
            child_entity=model.primary.stage_table,
            relationship_type="1:N",
            join_keys=["_file_name", "_file_sha256"],
            source_xpath=model.primary.path,
        )
    ]
    for ent in model.entities:
        parent_stage = ent.parent.stage_table if ent.parent else None
        parent_gold = ent.parent.curated_table if ent.parent else None
        stage_tables.append(
            LayerTableSpec(
                table_name=ent.stage_table,
                entity=ent.name,
                parent_table=parent_stage,
                foreign_keys=fks(ent, parent_stage),
                layer="STAGE",
                table_type="DYNAMIC_TABLE",
                ingestion_or_refresh="DYNAMIC_TABLE_REFRESH",
                upstream_source=mapping.targets.raw_table,
                target_lag="5 minutes",
                warehouse="COMPUTE_WH",
                grain=f"One row per {ent.path} element",
                primary_keys=[ent.pk_column],
                flatten_path=ent.path if ent.is_flattened else None,
                columns=[*key_columns(ent), *data_columns(ent, True), *sys_stage],
            )
        )
        gold_extra = (
            [
                LayerColumnSpec(name="_row_hash", snowflake_type="VARCHAR(64)", nullable=False),
                LayerColumnSpec(name="is_valid_start", snowflake_type="TIMESTAMP_NTZ", nullable=False),
                LayerColumnSpec(name="is_valid_end", snowflake_type="TIMESTAMP_NTZ", nullable=True),
                LayerColumnSpec(name="is_current", snowflake_type="BOOLEAN", nullable=False),
                LayerColumnSpec(name="system_start_time", snowflake_type="TIMESTAMP_NTZ", nullable=False),
                LayerColumnSpec(name="system_end_time", snowflake_type="TIMESTAMP_NTZ", nullable=True),
                LayerColumnSpec(name="_source_file", snowflake_type="VARCHAR(512)", nullable=False),
            ]
            if ent.parent is None
            else [
                LayerColumnSpec(name="_row_hash", snowflake_type="VARCHAR(64)", nullable=False),
                LayerColumnSpec(name="system_start_time", snowflake_type="TIMESTAMP_NTZ", nullable=False),
                LayerColumnSpec(name="_source_file", snowflake_type="VARCHAR(512)", nullable=False),
            ]
        )
        gold_tables.append(
            LayerTableSpec(
                table_name=ent.curated_table,
                entity=ent.name,
                parent_table=parent_gold,
                foreign_keys=fks(ent, parent_gold),
                layer="GOLD",
                table_type="DYNAMIC_TABLE",
                ingestion_or_refresh="DYNAMIC_TABLE_REFRESH",
                upstream_source=ent.stage_table,
                target_lag="15 minutes",
                warehouse="COMPUTE_WH",
                grain=(
                    f"Curated {ent.name} keyed by ({', '.join(ent.business_keys or [ent.pk_column])}) with version history"
                    if ent.parent is None
                    else f"Curated {ent.name} child rows of {ent.parent.name} (FK {ent.fk_column})"
                ),
                primary_keys=[ent.pk_column],
                flatten_path=None,
                columns=[*key_columns(ent), *data_columns(ent, False), *gold_extra],
            )
        )
        if ent.parent is not None:
            relationships.append(
                EntityRelationship(
                    parent_entity=ent.parent.stage_table,
                    child_entity=ent.stage_table,
                    relationship_type="1:N",
                    join_keys=[ent.fk_column or ""],
                    source_xpath=ent.path,
                    kind="FOREIGN_KEY",
                    layer="STAGE",
                    fk_column=ent.fk_column,
                    parent_pk_column=ent.parent.pk_column,
                )
            )
            relationships.append(
                EntityRelationship(
                    parent_entity=ent.parent.curated_table,
                    child_entity=ent.curated_table,
                    relationship_type="1:N",
                    join_keys=[ent.fk_column or ""],
                    source_xpath=ent.path,
                    kind="FOREIGN_KEY",
                    layer="GOLD",
                    fk_column=ent.fk_column,
                    parent_pk_column=ent.parent.pk_column,
                )
            )
        relationships.append(
            EntityRelationship(
                parent_entity=ent.stage_table,
                child_entity=ent.curated_table,
                relationship_type="1:1",
                join_keys=[ent.pk_column],
                source_xpath=ent.path,
            )
        )

    staging_schema = LayerSchemaYaml(
        dataset=ds,
        version=mapping.version,
        layer="STAGE",
        table_type="DYNAMIC_TABLE",
        tables=stage_tables,
        generated_by="step1_data_steward_agent",
        ddl_generated=False,
    )
    gold_schema = LayerSchemaYaml(
        dataset=ds,
        version=mapping.version,
        layer="GOLD",
        table_type="DYNAMIC_TABLE",
        tables=gold_tables,
        generated_by="step1_data_steward_agent",
        ddl_generated=False,
    )

    data_model = DataModelSpec(
        dataset=ds,
        version=mapping.version,
        root_element=mapping.root_element,
        business_keys=mapping.business_keys,
        entities=[raw_table_spec, *stage_tables, *gold_tables],
        relationships=relationships,
        approval_status="PENDING_HUMAN_APPROVAL",
        er_diagram_staging=render_er_diagram(model, "STAGE"),
        er_diagram_curated=render_er_diagram(model, "GOLD"),
    )

    return raw_schema, staging_schema, gold_schema, data_model

def run_data_steward_agent(
    manifest: OnboardingManifest,
    registry_root: Path,
    confidence_threshold: float = 0.8,
    llm_client: ClaudeClient | None = None,
) -> DatasetMapping:
    """Step 1: Read XML schema, create RAW YAML (no DDL), model Stage & Gold Dynamic Tables in YAML, and send for human approval.

    Uses Anthropic Claude (default: Haiku) for semantic modeling when ANTHROPIC_API_KEY is set; otherwise falls back
    to the rule-based model (or raises if `llm.fail_if_unavailable: true`).
    """
    sample_dir = Path(manifest.onboarding_sample_dir)
    xml_files = [sample_dir / fname for fname in manifest.valid_sample_files]

    mapping = infer_schema_from_xml_files(manifest.dataset, xml_files)
    ds_registry = registry_root / manifest.dataset
    ds_registry.mkdir(parents=True, exist_ok=True)

    # Remove any pre-existing ddl.sql so Step 1 strictly produces YAML schemas & data model (NOT DDL)
    ddl_path = ds_registry / "ddl.sql"
    if ddl_path.exists():
        ddl_path.unlink()

    # 1. Generate 3-layer YAML schemas (raw_schema.yaml, staging_schema.yaml, gold_schema.yaml) & data_model.yaml
    raw_schema, staging_schema, gold_schema, data_model = _build_three_layer_data_model(mapping)

    # 1b. Claude semantic modeling (descriptions, PII, entity grouping, Gold dimensional proposal)
    llm_cfg = load_llm_config()
    if llm_client is None and llm_cfg.is_available:
        llm_client = ClaudeClient(llm_cfg)
    if llm_client is not None:
        try:
            proposal = propose_data_model(mapping, llm_client)
            _apply_llm_proposal(proposal, [staging_schema, gold_schema], data_model, mapping)
        except LLMError as exc:
            if llm_cfg.fail_if_unavailable:
                raise
            logger.warning("Data Steward Agent: Claude modeling failed, using rule-based model: %s", exc)
            data_model.llm_note = f"Claude modeling failed; rule-based fallback used: {exc}"
    else:
        if llm_cfg.fail_if_unavailable:
            raise LLMError(f"LLM required but unavailable ({llm_cfg.api_key_env} not set or llm.enabled=false)")
        data_model.llm_note = (
            f"Claude not used ({llm_cfg.api_key_env} not set or llm.enabled=false); rule-based model generated."
        )

    (ds_registry / "raw_schema.yaml").write_text(
        yaml.safe_dump(raw_schema.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    (ds_registry / "staging_schema.yaml").write_text(
        yaml.safe_dump(staging_schema.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    (ds_registry / "gold_schema.yaml").write_text(
        yaml.safe_dump(gold_schema.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    (ds_registry / "data_model.yaml").write_text(
        yaml.safe_dump(data_model.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # 2. Write mapping.yaml (canonical field inventory)
    (ds_registry / "mapping.yaml").write_text(
        yaml.safe_dump(mapping.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # 3. Compute row counts across sample files for G2 Contract baseline
    row_counts: list[int] = []
    for xp in xml_files:
        rows = flatten_xml_to_rows(xp.read_text(encoding="utf-8"), mapping)
        row_counts.append(len(rows))

    contract = ContractSpec(
        dataset=manifest.dataset,
        version=mapping.version,
        root_element=mapping.root_element,
        required_xpaths=[f.xpath for f in mapping.fields if f.required],
        type_assertions={f.xpath: f.snowflake_type for f in mapping.fields},
        expected_rows_per_file_min=min(row_counts) if row_counts else 1,
        expected_rows_per_file_max=max(row_counts) * 5 if row_counts else 100,
        allow_unknown_elements=True,
    )
    (ds_registry / "contract.yaml").write_text(
        yaml.safe_dump(contract.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # 4. Generate G3 quality_rules.yaml stub
    accepted_vals: dict[str, list[str]] = {}
    ranges: list[RangeRule] = []
    for f in mapping.fields:
        if f.is_attribute and f.sample_values:
            accepted_vals[f.column] = sorted(set(f.sample_values))
        if f.snowflake_type.startswith("NUMBER") and not f.column.endswith("_id"):
            has_negative = any(float(v) < 0 for v in f.sample_values if v.strip())
            if not has_negative:
                ranges.append(RangeRule(column=f.column, min_value=0.0, max_value=None))

    quality_rules = QualityRulesSpec(
        dataset=manifest.dataset,
        version=mapping.version,
        primary_keys=mapping.business_keys,
        not_null_columns=[f.column for f in mapping.fields if f.required],
        accepted_values=accepted_vals,
        numeric_ranges=ranges,
        freshness_sla_hours=manifest.freshness_sla_hours,
    )
    (ds_registry / "quality_rules.yaml").write_text(
        yaml.safe_dump(quality_rules.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # 5. Write bootstrap_report.md for Human Approval Gate (C3)
    low_conf = [f for f in mapping.fields if f.confidence < confidence_threshold]
    report_lines = [
        f"# Step 1: Data Steward & Modeling Report — `{manifest.dataset}`",
        "",
        "> **Status:** Pending Human Approval (`PENDING_HUMAN_APPROVAL`). **No SQL DDL has been generated yet.**",
        "> Once approved at C3, the **DDL Generator Agent (Step 2)** will compile the Snowpipe and Dynamic Table SQLs.",
        "",
        "## Proposed 3-Layer Medallion Data Model (YAML Schemas)",
        "",
        "| Layer | YAML Schema File | Table Name | Snowflake Object Type | Ingestion / Refresh |",
        "|---|---|---|---|---|",
        f"| **1. RAW** | `raw_schema.yaml` | `{mapping.targets.raw_table}` | `NORMAL_TABLE` | `SNOWPIPE` (`ADLS -> RAW`) |",
        f"| **2. STAGE** | `staging_schema.yaml` | `{mapping.targets.staging_table}` | `DYNAMIC_TABLE` (`TARGET_LAG = '5 minutes'`) | `DYNAMIC_TABLE_REFRESH` (`RAW -> STAGE`) |",
        f"| **3. GOLD** | `gold_schema.yaml` | `{mapping.targets.curated_table}` | `DYNAMIC_TABLE` (`TARGET_LAG = '15 minutes'`) | `DYNAMIC_TABLE_REFRESH` (`STAGE -> GOLD`) |",
        "",
        f"- **Samples Analyzed:** {len(xml_files)} valid XML files",
        f"- **Root Element:** `{mapping.root_element}`",
        f"- **Inferred Business Keys:** `{', '.join(mapping.business_keys)}`",
        f"- **Total Inferred Fields:** {len(mapping.fields)} ({sum(1 for f in mapping.fields if f.is_array)} array fields)",
        f"- **Low-Confidence Fields (< {confidence_threshold}):** {len(low_conf)}",
        "",
        "## Inferred Field Inventory",
        "",
        "| XPath | Column | Snowflake Type | Required | Array (`LATERAL FLATTEN`) | Confidence | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in mapping.fields:
        status = "⚠️ Steward Review Needed" if f.confidence < confidence_threshold else "✅ High Confidence"
        report_lines.append(
            f"| `{f.xpath}` | `{f.column}` | `{f.snowflake_type}` | `{f.required}` | `{f.is_array}` | `{f.confidence:.2f}` | {status} |"
        )

    if low_conf:
        report_lines.extend([
            "",
            "## ⚠️ Low-Confidence Fields Flagged for C3 Steward Review",
            "",
        ])
        for f in low_conf:
            report_lines.append(
                f"- **`{f.column}`** (`{f.xpath}`): observed in {int(f.confidence * len(xml_files))}/{len(xml_files)} samples "
                f"(`confidence={f.confidence}`). Marked `required: false` with type `{f.snowflake_type}`."
            )

    report_lines.extend(["", "## Modeling Engine", ""])
    if data_model.llm_proposal is not None:
        prop = data_model.llm_proposal
        pii_cols = [a for a in prop.column_annotations if a.pii_category != "NONE"]
        renames = [a for a in prop.column_annotations if a.suggested_name]
        report_lines.extend([
            f"- **Engine:** Anthropic Claude (`{prop.model}`)",
            f"- **Columns annotated:** {len(prop.column_annotations)}/{len(mapping.fields)}",
            f"- **PII columns flagged:** {len(pii_cols)}",
            "",
            f"> {prop.summary}",
            "",
            "### Proposed Gold Dimensional Model (suggestion — review before approving)",
            "",
            "| Entity | Type | Grain | Primary Keys | Columns |",
            "|---|---|---|---|---|",
        ])
        for ent in prop.gold_entities:
            report_lines.append(
                f"| `{ent.name}` | {ent.entity_type} | {ent.grain} | `{', '.join(ent.primary_keys)}` | {len(ent.columns)} |"
            )
        if pii_cols:
            report_lines.extend(["", "### PII Columns", "", "| Column | Category | Description |", "|---|---|---|"])
            for a in pii_cols:
                report_lines.append(f"| `{a.column}` | {a.pii_category} | {a.description} |")
        if renames:
            report_lines.extend(["", "### Suggested Renames (not applied)", "", "| Current | Suggested |", "|---|---|"])
            for a in renames:
                report_lines.append(f"| `{a.column}` | `{a.suggested_name}` |")
        if prop.steward_review_notes:
            report_lines.extend(["", "### Claude Review Notes", ""])
            report_lines.extend(f"- {n}" for n in prop.steward_review_notes)
    else:
        report_lines.append(f"- **Engine:** Rule-based. {data_model.llm_note or ''}")

    (ds_registry / "bootstrap_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest.status = "BOOTSTRAPPED"
    (ds_registry / "onboarding_manifest.yaml").write_text(
        yaml.safe_dump(manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    return mapping


# Backward-compatible alias
run_c0_bootstrap = run_data_steward_agent
