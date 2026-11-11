"""Schema Diff and Migration Changelog Generator for Hierarchical Entity Models.

Compares an incoming XML feed or new mapping against the approved baseline
and produces a versioned CHANGELOG.md and non-breaking migration DDL script.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.entity_model import build_entity_model
from src.models import DatasetMapping, FieldMapping


@dataclass
class ColumnDiff:
    entity: str
    column: str
    change_type: str  # ADDED, DROPPED, TYPE_CHANGED
    old_type: str | None = None
    new_type: str | None = None
    xpath: str = ""


@dataclass
class EntityDiff:
    dataset: str
    from_version: str
    to_version: str
    added_entities: list[str] = field(default_factory=list)
    dropped_entities: list[str] = field(default_factory=list)
    column_diffs: list[ColumnDiff] = field(default_factory=list)
    migration_sqls: list[str] = field(default_factory=list)


def compare_mappings(
    baseline_mapping: DatasetMapping,
    current_mapping: DatasetMapping,
) -> EntityDiff:
    """Compares baseline vs current mapping and generates structural diff & migration SQL."""
    base_em = build_entity_model(baseline_mapping)
    curr_em = build_entity_model(current_mapping)

    base_entities = {e.name: e for e in base_em.entities}
    curr_entities = {e.name: e for e in curr_em.entities}

    added_ent = sorted(set(curr_entities.keys()) - set(base_entities.keys()))
    dropped_ent = sorted(set(base_entities.keys()) - set(curr_entities.keys()))

    column_diffs: list[ColumnDiff] = []
    migration_sqls: list[str] = []

    # Check for new entities
    for ent_name in added_ent:
        ent = curr_entities[ent_name]
        migration_sqls.append(
            f"-- ADD NEW CHILD ENTITY: {ent.stage_table}\n"
            f"-- (Compile through ddl_compiler.py for LATERAL FLATTEN & surrogate PK/FK)"
        )

    # Check columns in common entities
    for ent_name, curr_e in curr_entities.items():
        if ent_name in base_entities:
            base_e = base_entities[ent_name]
            base_cols = {c.name: c for c in base_e.columns}
            curr_cols = {c.name: c for c in curr_e.columns}

            # Added columns
            for col_name, c in curr_cols.items():
                if col_name not in base_cols:
                    column_diffs.append(
                        ColumnDiff(
                            entity=ent_name,
                            column=col_name,
                            change_type="ADDED",
                            new_type=c.field.snowflake_type,
                            xpath=c.field.xpath,
                        )
                    )
                    migration_sqls.append(
                        f"ALTER DYNAMIC TABLE IF EXISTS ENTERPRISE_DW.STAGING.{curr_e.stage_table.upper()} "
                        f"ADD COLUMN IF NOT EXISTS {col_name} {c.field.snowflake_type};"
                    )

            # Type changes
            for col_name, c in curr_cols.items():
                if col_name in base_cols:
                    old_t = base_cols[col_name].field.snowflake_type
                    new_t = c.field.snowflake_type
                    if old_t != new_t:
                        column_diffs.append(
                            ColumnDiff(
                                entity=ent_name,
                                column=col_name,
                                change_type="TYPE_CHANGED",
                                old_type=old_t,
                                new_type=new_t,
                                xpath=c.field.xpath,
                            )
                        )
                        migration_sqls.append(
                            f"-- TYPE CHANGE on {curr_e.stage_table}.{col_name}: {old_t} -> {new_t}\n"
                            f"ALTER DYNAMIC TABLE IF EXISTS ENTERPRISE_DW.STAGING.{curr_e.stage_table.upper()} "
                            f"ALTER COLUMN {col_name} SET DATA TYPE {new_t};"
                        )

    return EntityDiff(
        dataset=current_mapping.dataset,
        from_version=baseline_mapping.version,
        to_version=current_mapping.version,
        added_entities=added_ent,
        dropped_entities=dropped_ent,
        column_diffs=column_diffs,
        migration_sqls=migration_sqls,
    )


def generate_changelog_markdown(diff: EntityDiff) -> str:
    """Renders the EntityDiff into a clean, GitHub-flavored Markdown changelog."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [
        f"# Schema Evolution Changelog — `{diff.dataset}`",
        f"- **Migration:** `v{diff.from_version}` &rarr; `v{diff.to_version}`",
        f"- **Generated At:** `{now}`",
        "",
        "## 1. Summary of Changes",
        f"- **New Child Entities:** {len(diff.added_entities)} (`{', '.join(diff.added_entities) if diff.added_entities else 'None'}`)",
        f"- **Retired Entities:** {len(diff.dropped_entities)} (`{', '.join(diff.dropped_entities) if diff.dropped_entities else 'None'}`)",
        f"- **Modified / Added Columns:** {len(diff.column_diffs)}",
        "",
        "## 2. Detailed Column Changes",
        "| Entity | Column | Change Type | Old Type | New Type | XPath Source |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    if not diff.column_diffs and not diff.added_entities:
        lines.append("| *No column modifications detected* | - | - | - | - | - |")
    else:
        for cd in diff.column_diffs:
            lines.append(
                f"| `{cd.entity}` | `{cd.column}` | **{cd.change_type}** | `{cd.old_type or '-'}` | `{cd.new_type or '-'}` | `{cd.xpath}` |"
            )

    lines.extend([
        "",
        "## 3. Recommended Migration SQL Script",
        "```sql",
    ])
    if diff.migration_sqls:
        lines.extend(diff.migration_sqls)
    else:
        lines.append("-- No DDL schema migrations required. All models are up to date.")
    lines.append("```")

    return "\n".join(lines) + "\n"
