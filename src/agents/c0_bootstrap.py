"""Stage 2 — C0: Schema Bootstrap Agent.

Infers mapping.yaml, ddl.sql, contract.yaml (G2), quality_rules.yaml (G3), and
bootstrap_report.md directly from representative sample XML files (no XSD required).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from src.ddl_compiler import compile_snowflake_ddl
from src.models import (
    ContractSpec,
    DatasetMapping,
    OnboardingManifest,
    QualityRulesSpec,
    RangeRule,
)
from src.xml_infer import flatten_xml_to_rows, infer_schema_from_xml_files


def run_c0_bootstrap(
    manifest: OnboardingManifest,
    registry_root: Path,
    confidence_threshold: float = 0.8,
) -> DatasetMapping:
    """Run C0 schema inference on all valid sample XMLs and emit C4 registry artefacts."""
    sample_dir = Path(manifest.onboarding_sample_dir)
    xml_files = [sample_dir / fname for fname in manifest.valid_sample_files]

    mapping = infer_schema_from_xml_files(manifest.dataset, xml_files)
    ds_registry = registry_root / manifest.dataset
    ds_registry.mkdir(parents=True, exist_ok=True)

    # 1. Write mapping.yaml
    (ds_registry / "mapping.yaml").write_text(
        yaml.safe_dump(mapping.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # 2. Write ddl.sql
    ddl_sql = compile_snowflake_ddl(mapping)
    (ds_registry / "ddl.sql").write_text(ddl_sql, encoding="utf-8")

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

    # 5. Write bootstrap_report.md for Stage 3 (C3 Data Steward Review)
    low_conf = [f for f in mapping.fields if f.confidence < confidence_threshold]
    report_lines = [
        f"# C0 Schema Bootstrap Report — `{manifest.dataset}`",
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

    (ds_registry / "bootstrap_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest.status = "BOOTSTRAPPED"
    (ds_registry / "onboarding_manifest.yaml").write_text(
        yaml.safe_dump(manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    return mapping
