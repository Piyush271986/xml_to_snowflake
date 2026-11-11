"""Looker LookML View and Explore Exporter derived from an EntityModel."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.entity_model import EntityModel, Entity


def _map_sf_to_lookml_type(sf_type: str) -> str:
    t = sf_type.upper()
    if "NUMBER" in t or "INT" in t or "FLOAT" in t or "DECIMAL" in t:
        return "number"
    elif "DATE" in t:
        return "date"
    elif "TIME" in t:
        return "date_time"
    elif "BOOLEAN" in t:
        return "yesno"
    return "string"


def export_lookml_project(entity_model: EntityModel, output_dir: Path) -> dict[str, Any]:
    """Generates LookML views and an explore definition with joins for all entities."""
    output_dir.mkdir(parents=True, exist_ok=True)
    views_dir = output_dir / "views"
    views_dir.mkdir(parents=True, exist_ok=True)

    generated_views: list[str] = []

    # 1. Generate LookML View for each entity
    for ent in entity_model.entities:
        view_name = ent.name
        table_name = ent.curated_table or ent.stage_table
        lines: list[str] = [
            f"view: {view_name} {{",
            f"  sql_table_name: ENTERPRISE_DW.CURATED.{table_name.upper()} ;;",
            "",
            f"  dimension: {ent.name}_pk {{",
            "    primary_key: yes",
            "    type: string",
            f"    sql: ${{TABLE}}.{ent.name}_pk ;;",
            "  }",
        ]

        if ent.parent:
            lines.extend([
                "",
                f"  dimension: {ent.parent.name}_fk {{",
                "    type: string",
                f"    sql: ${{TABLE}}.{ent.parent.name}_fk ;;",
                "  }",
            ])

        for col in ent.columns:
            l_type = _map_sf_to_lookml_type(col.field.snowflake_type)
            lines.extend([
                "",
                f"  dimension: {col.name} {{",
                f"    type: {l_type}",
                f"    description: \"XPath: {col.field.xpath}\"",
                f"    sql: ${{TABLE}}.{col.name} ;;",
                "  }",
            ])

        lines.extend([
            "",
            "  measure: count {",
            "    type: count",
            "    drill_fields: [detail*]",
            "  }",
            "",
            f"  set: detail {{ fields: [{ent.name}_pk{f', {ent.parent.name}_fk' if ent.parent else ''}] }}",
            "}",
            "",
        ])

        view_file = views_dir / f"{view_name}.view.lkml"
        view_file.write_text("\n".join(lines), encoding="utf-8")
        generated_views.append(view_name)

    # 2. Generate Master Explore with 1:N Joins
    root_ent = next((e for e in entity_model.entities if e.kind in ("RECORD", "DOCUMENT")), entity_model.entities[0])
    explore_lines: list[str] = [
        f"include: \"/views/*.view.lkml\"",
        "",
        f"explore: {root_ent.name} {{",
        f"  label: \"{entity_model.dataset.title()} Reference Model\"",
        f"  description: \"Golden curated layer for {entity_model.dataset} securities data\"",
        "",
    ]

    for ent in entity_model.entities:
        if ent != root_ent and ent.parent:
            explore_lines.extend([
                f"  join: {ent.name} {{",
                "    type: left_outer",
                "    relationship: one_to_many",
                f"    sql_on: ${{TABLE}}.{ent.parent.name}_pk = ${{{ent.name}}}.{ent.parent.name}_fk ;;",
                "  }",
                "",
            ])

    explore_lines.append("}\n")
    explore_file = output_dir / f"{entity_model.dataset}.explore.lkml"
    explore_file.write_text("\n".join(explore_lines), encoding="utf-8")

    return {
        "explore_file": str(explore_file),
        "views_dir": str(views_dir),
        "views_count": len(generated_views),
        "views": generated_views,
    }
