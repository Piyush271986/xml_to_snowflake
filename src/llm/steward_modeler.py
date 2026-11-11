"""Claude-backed data modeling for the Step 1 Data Steward Agent.

Claude receives the deterministically-inferred field inventory (XPaths, types, cardinality, confidence)
and returns:
  - per-column business descriptions, semantic entity grouping, PII category and optional rename suggestions
  - a proposed Gold-layer dimensional model (facts / dimensions) for human review
  - steward review notes

Claude's output is validated against the real field inventory: unknown columns are dropped and nothing
it returns changes executable XPaths, types or column names. Renames and Gold entities are recorded as
suggestions for the C3 human approval gate.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from src.llm.anthropic_client import ClaudeClient, LLMError
from src.models import DatasetMapping, LLMModelingProposal

logger = logging.getLogger(__name__)

TOOL_NAME = "submit_data_model"

SYSTEM_PROMPT = """You are a senior data steward and dimensional data modeler for a Snowflake medallion platform.
The pipeline is fixed: ADLS XML -> Snowpipe -> RAW normal table (VARIANT) -> STAGE Dynamic Table (typed, flattened) -> GOLD Dynamic Table.
You are given a field inventory that was inferred deterministically from sample XML files. Types, XPaths and cardinality are facts; do not change them.
The pipeline deterministically explodes every repeating XML element (see flatten_path) into its own parent/child table linked by a surrogate PK/FK, so describe each column in the context of its owning entity and do not re-flatten children into parents.
Your job:
1. For EVERY column in the inventory, write a concise business description (max 20 words), assign a semantic_entity (snake_case business entity such as order_header, customer, line_item, payment, shipment, audit_event), classify PII, and optionally suggest a clearer snake_case name only when the current name is ambiguous.
2. Propose a GOLD-layer dimensional model (facts and dimensions). Use only column names from the inventory. Give each entity a clear grain and primary keys.
3. List concrete review notes for the human data steward (e.g. low-confidence fields, PII handling, questionable keys).
Always respond by calling the submit_data_model tool. Never invent columns."""

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "2-4 sentence summary of the proposed model."},
        "column_annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "column": {"type": "string"},
                    "description": {"type": "string"},
                    "semantic_entity": {"type": "string"},
                    "pii_category": {
                        "type": "string",
                        "enum": ["NONE", "CONTACT", "FINANCIAL", "GOVERNMENT_ID", "LOCATION", "OTHER"],
                    },
                    "suggested_name": {"type": ["string", "null"]},
                },
                "required": ["column", "description", "semantic_entity", "pii_category"],
            },
        },
        "gold_entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "entity_type": {"type": "string", "enum": ["FACT", "DIMENSION", "BRIDGE", "SATELLITE"]},
                    "grain": {"type": "string"},
                    "primary_keys": {"type": "array", "items": {"type": "string"}},
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": ["name", "entity_type", "grain", "primary_keys", "columns"],
            },
        },
        "steward_review_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "column_annotations", "gold_entities", "steward_review_notes"],
}


def _build_prompt(mapping: DatasetMapping, send_sample_values: bool) -> str:
    inventory = []
    for f in mapping.fields:
        item: dict[str, Any] = {
            "column": f.column,
            "xpath": f.xpath,
            "type": f.snowflake_type,
            "required": f.required,
            "is_array": f.is_array,
            "flatten_path": f.flatten_path,
            "is_attribute": f.is_attribute,
            "confidence": f.confidence,
        }
        if send_sample_values:
            item["samples"] = f.sample_values[:3]
        inventory.append(item)

    return (
        f"Dataset: {mapping.dataset}\n"
        f"Root element: {mapping.root_element}\n"
        f"Inferred business keys: {mapping.business_keys}\n"
        f"Stage table: {mapping.targets.staging_table} | Gold table: {mapping.targets.curated_table}\n"
        f"Field inventory ({len(inventory)} columns, JSON):\n"
        f"{json.dumps(inventory, separators=(',', ':'))}"
    )


def _sanitize(raw: dict[str, Any], mapping: DatasetMapping, model: str) -> tuple[LLMModelingProposal, list[str]]:
    """Validate Claude's output against the real inventory; drop anything referencing unknown columns."""
    known = {f.column for f in mapping.fields}
    warnings: list[str] = []

    annotations = []
    seen: set[str] = set()
    for ann in raw.get("column_annotations") or []:
        col = (ann or {}).get("column")
        if col not in known:
            warnings.append(f"Dropped annotation for unknown column '{col}'")
            continue
        if col in seen:
            continue
        seen.add(col)
        sug = ann.get("suggested_name")
        if sug and (sug == col or sug in known):
            ann["suggested_name"] = None
        annotations.append(ann)

    missing = sorted(known - seen)
    if missing:
        warnings.append(f"Claude did not annotate {len(missing)} column(s): {', '.join(missing[:10])}")

    entities = []
    for ent in raw.get("gold_entities") or []:
        cols = [c for c in (ent or {}).get("columns", []) if c in known]
        pks = [c for c in ent.get("primary_keys", []) if c in known]
        dropped = len(ent.get("columns", [])) - len(cols)
        if dropped:
            warnings.append(f"Gold entity '{ent.get('name')}': dropped {dropped} unknown column reference(s)")
        if not cols:
            warnings.append(f"Dropped Gold entity '{ent.get('name')}' (no valid columns)")
            continue
        ent["columns"], ent["primary_keys"] = cols, pks
        entities.append(ent)

    proposal = LLMModelingProposal.model_validate(
        {
            "model": model,
            "summary": raw.get("summary", ""),
            "column_annotations": annotations,
            "gold_entities": entities,
            "steward_review_notes": list(raw.get("steward_review_notes") or []) + warnings,
        }
    )
    return proposal, warnings


def propose_data_model(mapping: DatasetMapping, client: ClaudeClient) -> LLMModelingProposal:
    """Ask Claude for a data model proposal and return a validated LLMModelingProposal."""
    raw = client.call_tool(
        system=SYSTEM_PROMPT,
        prompt=_build_prompt(mapping, client.config.send_sample_values),
        tool_name=TOOL_NAME,
        tool_description="Submit the column annotations, Gold dimensional model and steward review notes.",
        input_schema=INPUT_SCHEMA,
    )
    try:
        proposal, warnings = _sanitize(raw, mapping, client.model)
    except ValidationError as exc:
        raise LLMError(f"Claude returned a data model that failed validation: {exc}") from exc
    for w in warnings:
        logger.warning("Data Steward Agent (Claude): %s", w)
    return proposal

