"""Export OpenAPI 3.1 Specification and JSON Schema derived from an EntityModel."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.entity_model import EntityModel, Entity


def _map_sf_type_to_json_schema(sf_type: str) -> dict[str, str]:
    t = sf_type.upper()
    if "INT" in t or "NUMBER" in t:
        if "," in t and not t.endswith(",0)"):
            return {"type": "number"}
        return {"type": "integer"}
    elif "BOOLEAN" in t:
        return {"type": "boolean"}
    elif "DATE" in t:
        return {"type": "string", "format": "date"}
    elif "TIME" in t:
        return {"type": "string", "format": "date-time"}
    return {"type": "string"}


def export_json_schema(entity_model: EntityModel, output_path: Path) -> dict[str, Any]:
    """Compile the hierarchical entity graph into a nested JSON Schema document."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    definitions: dict[str, Any] = {}

    for ent in entity_model.entities:
        properties: dict[str, Any] = {
            f"{ent.name}_pk": {
                "type": "string",
                "description": f"Surrogate primary key for entity {ent.name}",
            }
        }
        required: list[str] = [f"{ent.name}_pk"]

        if ent.parent:
            properties[f"{ent.parent.name}_fk"] = {
                "type": "string",
                "description": f"Foreign key referencing {ent.parent.name}.{ent.parent.name}_pk",
            }
            required.append(f"{ent.parent.name}_fk")

        for col in ent.columns:
            prop = _map_sf_type_to_json_schema(col.field.snowflake_type)
            prop["description"] = f"XPath: {col.field.xpath}"
            properties[col.name] = prop
            if col.field.required:
                required.append(col.name)

        definitions[ent.name] = {
            "type": "object",
            "title": ent.name.title(),
            "description": f"{ent.kind} entity mapped from XML tag <{ent.tag}>",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    # Find the root document entity
    root_ent = next((e for e in entity_model.entities if e.kind == "DOCUMENT"), entity_model.entities[0])
    
    schema_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://enterprise.io/schemas/{entity_model.dataset}.json",
        "title": f"{entity_model.dataset.title()} Data Contract",
        "type": "object",
        "description": f"Hierarchical data contract for dataset {entity_model.dataset}",
        "$ref": f"#/$defs/{root_ent.name}",
        "$defs": definitions,
    }

    output_path.write_text(json.dumps(schema_doc, indent=2), encoding="utf-8")
    return schema_doc


def export_openapi_spec(entity_model: EntityModel, output_path: Path) -> dict[str, Any]:
    """Compile the entity model into an OpenAPI 3.1 REST API specification."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    json_schema = export_json_schema(entity_model, output_path.with_suffix(".json_schema.json"))
    schemas = json_schema["$defs"]

    paths: dict[str, Any] = {}
    for ent in entity_model.entities:
        paths[f"/api/v1/{ent.name}"] = {
            "get": {
                "summary": f"List {ent.name} records",
                "operationId": f"list_{ent.name}",
                "parameters": [
                    {
                        "name": f"{ent.parent.name}_fk" if ent.parent else f"{ent.name}_pk",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Filter by key",
                    }
                ],
                "responses": {
                    "200": {
                        "description": f"Array of {ent.name} items",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": f"#/components/schemas/{ent.name}"},
                                }
                            }
                        },
                    }
                },
            }
        }

    openapi_doc = {
        "openapi": "3.1.0",
        "info": {
            "title": f"{entity_model.dataset.title()} Service API",
            "version": "1.0.0",
            "description": f"REST endpoints exposing curated entities for {entity_model.dataset}",
        },
        "paths": paths,
        "components": {"schemas": schemas},
    }

    output_path.write_text(json.dumps(openapi_doc, indent=2), encoding="utf-8")
    return openapi_doc
