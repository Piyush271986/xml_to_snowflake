"""Control Plane — C2: Proposal Agent.

Implements the Change Policy:
- Additive drift (only NEW_OPTIONAL_ELEMENT findings): Auto-applies nullable columns to
  mapping.yaml, contract.yaml, ddl.sql, and local warehouse tables.
- Breaking drift (any MISSING_REQUIRED_ELEMENT or TYPE_INCOMPATIBLE finding): Looks up
  downstream lineage impact from DataHub URNs ('Read at C3: impact check') and writes a
  human review proposal for C3 Approval without mutating production tables.
"""
from __future__ import annotations

from contextlib import closing
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.agents.a1_provision import _sf_type_to_sqlite
from src.ddl_compiler import compile_additive_drift_sql, compile_snowflake_ddl
from src.models import (
    ContractSpec,
    DatasetMapping,
    DriftFinding,
    DriftProposal,
    FieldMapping,
)
from src.xml_infer import build_column_name, build_snowflake_xml_expr


def _bump_version(version: str, breaking: bool) -> str:
    parts = [int(x) for x in version.split(".")]
    while len(parts) < 3:
        parts.append(0)
    if breaking:
        return f"{parts[0] + 1}.0.0"
    return f"{parts[0]}.{parts[1] + 1}.0"


def handle_drift_findings(
    dataset: str,
    registry_root: Path,
    findings: list[DriftFinding],
) -> DriftProposal:
    """Process C1 drift findings according to the Control Plane Change Policy."""
    ds_registry = registry_root / dataset
    mapping = DatasetMapping.model_validate(
        yaml.safe_load((ds_registry / "mapping.yaml").read_text(encoding="utf-8"))
    )
    contract = ContractSpec.model_validate(
        yaml.safe_load((ds_registry / "contract.yaml").read_text(encoding="utf-8"))
    )

    additive = [f for f in findings if f.classification == "ADDITIVE"]
    breaking = [f for f in findings if f.classification == "BREAKING"]
    has_breaking = len(breaking) > 0
    next_version = _bump_version(mapping.version, breaking=has_breaking)
    now = datetime.now(timezone.utc).isoformat()

    # Read at C3: impact check from DataHub catalog registration
    downstream_impact: list[str] = []
    dh_path = ds_registry / "datahub_urns.yaml"
    if dh_path.exists():
        dh_data = yaml.safe_load(dh_path.read_text(encoding="utf-8"))
        entities = dh_data.get("entities", {})
        owners = dh_data.get("owners", {})
        downstream_impact = [
            f"Staging Table: {entities.get('d3_staging')}",
            f"Curated SCD2 Table: {entities.get('d4_curated')}",
            f"SLA Dashboard: v_sla_dashboard_{dataset}",
            f"Data Steward: {owners.get('data_steward')}",
            f"Engineering Owner: {owners.get('data_engineering')}",
        ]

    root_tag = mapping.root_element.strip("/")
    new_field_mappings: list[FieldMapping] = []
    for add in additive:
        sf_type = add.observed_type or "VARCHAR"
        col_name = build_column_name(add.xpath, root_tag, flatten_path=None)
        xml_expr = build_snowflake_xml_expr(
            xpath=add.xpath,
            root_tag=root_tag,
            sf_type=sf_type,
            is_array=False,
            flatten_path=None,
            is_attribute=add.xpath.split("/")[-1].startswith("@"),
        )
        new_field_mappings.append(
            FieldMapping(
                xpath=add.xpath,
                column=col_name,
                snowflake_type=sf_type,
                xml_expr=xml_expr,
                required=False,
                is_array=False,
                flatten_path=None,
                is_attribute=add.xpath.split("/")[-1].startswith("@"),
                confidence=0.1,
                sample_values=[add.sample_value] if add.sample_value else [],
                origin="c1_drift_additive",
                added_in_version=next_version,
            )
        )

    proposed_sql = compile_additive_drift_sql(dataset, new_field_mappings)

    if not has_breaking and new_field_mappings:
        # AUTO-APPLY ADDITIVE DRIFT
        mapping.version = next_version
        mapping.fields.extend(new_field_mappings)
        (ds_registry / "mapping.yaml").write_text(
            yaml.safe_dump(mapping.model_dump(), sort_keys=False),
            encoding="utf-8",
        )

        contract.version = next_version
        for nf in new_field_mappings:
            contract.type_assertions[nf.xpath] = nf.snowflake_type
        (ds_registry / "contract.yaml").write_text(
            yaml.safe_dump(contract.model_dump(), sort_keys=False),
            encoding="utf-8",
        )

        (ds_registry / "ddl.sql").write_text(compile_snowflake_ddl(mapping), encoding="utf-8")

        # Apply ALTER TABLE ADD COLUMN to local warehouse simulation DB
        db_path = ds_registry / "local_warehouse.db"
        if db_path.exists():
            with closing(sqlite3.connect(db_path)) as conn:
                cur = conn.cursor()
                for nf in new_field_mappings:
                    sqlite_type = _sf_type_to_sqlite(nf.snowflake_type)
                    cur.execute(
                        f"ALTER TABLE {mapping.targets.staging_table} ADD COLUMN {nf.column} {sqlite_type};"
                    )
                    cur.execute(
                        f"ALTER TABLE {mapping.targets.curated_table} ADD COLUMN {nf.column} {sqlite_type};"
                    )
                conn.commit()

        status = "AUTO_APPLIED"
    else:
        status = "PENDING_C3_APPROVAL"
        for brk in breaking:
            if brk.change_type == "TYPE_INCOMPATIBLE":
                col = build_column_name(brk.xpath, root_tag, None)
                proposed_sql.append(
                    f"-- BREAKING: widen {col} from {brk.expected_type} to {brk.observed_type}\n"
                    f"ALTER TABLE staging_{dataset} ALTER COLUMN {col} SET DATA TYPE {brk.observed_type};"
                )
            elif brk.change_type == "MISSING_REQUIRED_ELEMENT":
                col = build_column_name(brk.xpath, root_tag, None)
                proposed_sql.append(
                    f"-- BREAKING: drop NOT NULL / required contract on {brk.xpath} ({col})\n"
                    f"ALTER TABLE staging_{dataset} ALTER COLUMN {col} DROP NOT NULL;"
                )

    proposal = DriftProposal(
        dataset=dataset,
        current_version=mapping.version if has_breaking else _bump_version(next_version, False),
        proposed_version=next_version,
        status=status,
        additive_findings=additive,
        breaking_findings=breaking,
        proposed_sql=proposed_sql,
        downstream_impact=downstream_impact,
        created_at=now,
    )

    proposals_dir = ds_registry / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
    proposal_file = proposals_dir / f"proposal_{next_version}.md"

    md_lines = [
        f"# C2 Schema Drift Proposal — `{dataset}` (`v{next_version}`)",
        "",
        f"- **Status:** `{proposal.status}`",
        f"- **Created At:** `{now}`",
        "",
        "## Drift Findings",
        "",
        "| XPath | Change Type | Classification | Expected | Observed | Sample Value | Source File |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in findings:
        md_lines.append(
            f"| `{f.xpath}` | `{f.change_type}` | **{f.classification}** | "
            f"`{f.expected_type or '-'}` | `{f.observed_type or '-'}` | `{f.sample_value or '-'}` | `{f.source_file}` |"
        )

    md_lines.extend([
        "",
        "## Proposed Snowflake DDL Changes",
        "",
        "```sql",
        *proposed_sql,
        "```",
        "",
        "## Downstream Impact (Read from DataHub at C3)",
        "",
        *[f"- {imp}" for imp in downstream_impact],
    ])
    proposal_file.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return proposal
