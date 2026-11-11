"""Export dbt (data build tool) sources, staging models, and schema YAML from an EntityModel."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from src.entity_model import EntityModel, Entity


def export_dbt_project(entity_model: EntityModel, output_dir: Path) -> dict[str, Any]:
    """Generates dbt schema.yml and staging SQL models for all entities in the hierarchy."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stg_dir = output_dir / "models" / "staging"
    stg_dir.mkdir(parents=True, exist_ok=True)

    models_meta: list[dict[str, Any]] = []

    for ent in entity_model.entities:
        model_name = f"stg_{ent.name}"
        pk_name = f"{ent.name}_pk"
        cols_meta: list[dict[str, Any]] = [
            {
                "name": pk_name,
                "description": f"Surrogate primary key for {ent.name}",
                "tests": ["unique", "not_null"],
            }
        ]

        if ent.parent:
            fk_name = f"{ent.parent.name}_fk"
            cols_meta.append({
                "name": fk_name,
                "description": f"Foreign key referencing stg_{ent.parent.name}.{ent.parent.name}_pk",
                "tests": [
                    "not_null",
                    {
                        "relationships": {
                            "to": f"ref('stg_{ent.parent.name}')",
                            "field": f"{ent.parent.name}_pk",
                        }
                    },
                ],
            })

        for col in ent.columns:
            col_meta: dict[str, Any] = {
                "name": col.name,
                "description": f"Extracted from XML XPath: {col.field.xpath}",
            }
            if col.field.required:
                col_meta["tests"] = ["not_null"]
            cols_meta.append(col_meta)

        models_meta.append({
            "name": model_name,
            "description": f"Staging model for {ent.kind.lower()} entity `{ent.name}`",
            "columns": cols_meta,
        })

        # Generate dbt SQL model pointing to Snowflake raw / staging table
        sql_content = f"""-- Staging dbt model for {ent.name}
{{{{ config(materialized='view') }}}}

SELECT
    {pk_name},
    {f'{ent.parent.name}_fk,' if ent.parent else ''}
    {', '.join([c.name for c in ent.columns])}
FROM {{{{ source('snowflake_dw', '{ent.stage_table}') }}}}
"""
        (stg_dir / f"{model_name}.sql").write_text(sql_content, encoding="utf-8")

    schema_yml = {
        "version": 2,
        "sources": [
            {
                "name": "snowflake_dw",
                "database": "ENTERPRISE_DW",
                "schema": "STAGING",
                "tables": [{"name": ent.stage_table} for ent in entity_model.entities],
            }
        ],
        "models": models_meta,
    }

    schema_path = stg_dir / "schema.yml"
    schema_path.write_text(yaml.dump(schema_yml, sort_keys=False), encoding="utf-8")

    return {
        "schema_path": str(schema_path),
        "models_count": len(models_meta),
        "models": [m["name"] for m in models_meta],
    }
