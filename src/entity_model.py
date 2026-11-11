"""Hierarchical entity model derived from the inferred XML field inventory.

Every repeating XML element (``<ASSET>``, ``<CUSIP2_record>``, ``<LineItem>`` ...) becomes its own entity
(one table per layer) instead of being flattened into one wide parent table. Single-occurrence wrapper
elements (``<BND_CORP>``, ``<CUSIP2_set>``) are structural only: their leaf fields belong to the nearest
enclosing entity. Each child entity carries a deterministic foreign key (``<parent>_fk``) pointing at its
parent's primary key (``<parent>_pk``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from src.models import DatasetMapping, FieldMapping
from src.xml_infer import to_snake_case

_ENTITY_SUFFIXES = ("_record", "_item")
_SET_SIZE_ATTRS = {"size", "count"}
_RESERVED_WORDS = {
    "all", "any", "as", "by", "case", "class", "current", "delete", "else", "end", "from", "group", "having", "if",
    "in", "insert", "is", "join", "limit", "not", "null", "on", "order", "select", "table", "then", "union", "update",
    "user", "values", "when", "where", "with",
}


@dataclass
class EntityColumn:
    name: str
    field: FieldMapping
    element_parts: list[str]  # element path relative to the owning entity (wrappers only, leaf excluded for attributes)
    attribute: str | None  # attribute name when the column is an XML attribute
    from_document: bool = False  # True for document-root attributes folded into the top record entity


@dataclass
class Entity:
    name: str
    tag: str
    path: str
    kind: Literal["DOCUMENT", "RECORD", "CHILD"]
    parent: "Entity | None" = None
    columns: list[EntityColumn] = field(default_factory=list)
    stage_table: str = ""
    curated_table: str = ""
    business_keys: list[str] = field(default_factory=list)

    @property
    def is_flattened(self) -> bool:
        """True when rows come from a LATERAL FLATTEN over a repeating element."""
        return self.kind != "DOCUMENT"

    @property
    def pk_column(self) -> str:
        return f"{self.name}_pk"

    @property
    def fk_column(self) -> str | None:
        return f"{self.parent.name}_fk" if self.parent else None

    def chain(self) -> list["Entity"]:
        """Ancestors (root first) ending with this entity."""
        out: list[Entity] = []
        node: Entity | None = self
        while node is not None:
            out.append(node)
            node = node.parent
        return list(reversed(out))


@dataclass
class EntityModel:
    dataset: str
    root_path: str
    entities: list[Entity]  # parent-first order

    @property
    def primary(self) -> Entity:
        return self.entities[0]

    def children_of(self, entity: Entity) -> list[Entity]:
        return [e for e in self.entities if e.parent is entity]


def _parts(path: str) -> list[str]:
    return [p for p in path.strip("/").split("/") if p]


def _entity_name(tag: str) -> str:
    name = to_snake_case(tag)
    for suffix in _ENTITY_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
            break
    return name


def build_entity_model(mapping: DatasetMapping) -> EntityModel:
    """Group the flat field inventory into parent / child entities."""
    root_parts = _parts(mapping.root_element)
    root_path = "/" + "/".join(root_parts)
    ds = mapping.dataset

    rep_paths = sorted(
        {f.flatten_path for f in mapping.fields if f.flatten_path},
        key=lambda p: (len(_parts(p)), p),
    )
    wrapper_parents = {"/" + "/".join(_parts(p)[:-1]) for p in rep_paths}

    def keep(f: FieldMapping) -> bool:
        # Drop `<X_set SIZE="n">` bookkeeping attributes of wrappers whose children became entities
        parts = _parts(f.xpath)
        if f.is_attribute and parts and parts[-1][1:].lower() in _SET_SIZE_ATTRS:
            return "/" + "/".join(parts[:-1]) not in wrapper_parents
        return True

    fields = [f for f in mapping.fields if keep(f)]
    doc_fields = [f for f in fields if not f.flatten_path]

    def nearest_ancestor(path: str) -> str | None:
        p = _parts(path)
        for cut in range(len(p) - 1, 0, -1):
            cand = "/" + "/".join(p[:cut])
            if cand in rep_paths:
                return cand
        return None

    top_level = [p for p in rep_paths if nearest_ancestor(p) is None]
    fold_document = bool(
        doc_fields
        and all(f.is_attribute for f in doc_fields)
        and len(top_level) == 1
        and len(_parts(top_level[0])) == len(root_parts) + 1
    )

    entities: list[Entity] = []
    by_path: dict[str, Entity] = {}
    used_names: set[str] = set()

    def unique_name(tag: str, parent: Entity | None) -> str:
        name = _entity_name(tag)
        if name in used_names and parent is not None:
            name = f"{parent.name}_{name}"
        base, idx = name, 2
        while name in used_names:
            name = f"{base}_{idx}"
            idx += 1
        used_names.add(name)
        return name

    if doc_fields and not fold_document or not rep_paths:
        doc = Entity(name=unique_name(root_parts[-1], None), tag=root_parts[-1], path=root_path, kind="DOCUMENT")
        entities.append(doc)
        by_path[root_path] = doc

    for path in rep_paths:
        anc = nearest_ancestor(path)
        parent = by_path.get(anc) if anc else by_path.get(root_path)
        tag = _parts(path)[-1]
        kind: Literal["DOCUMENT", "RECORD", "CHILD"] = "RECORD" if parent is None or parent.kind == "DOCUMENT" else "CHILD"
        ent = Entity(name=unique_name(tag, parent), tag=tag, path=path, kind=kind, parent=parent)
        entities.append(ent)
        by_path[path] = ent

    colname_by_field: dict[str, str] = {}
    used_cols: dict[str, set[str]] = {e.path: set() for e in entities}

    def add_column(ent: Entity, f: FieldMapping, from_document: bool) -> None:
        col = f.column
        if ent.kind != "DOCUMENT" and not from_document:
            prefix = to_snake_case(ent.tag) + "_"
            if col.startswith(prefix) and len(col) > len(prefix):
                col = col[len(prefix):]
        if col.lower() in _RESERVED_WORDS:
            col = f"{col}_val"
        base, idx = col, 2
        while col in used_cols[ent.path] or col in (ent.pk_column, ent.fk_column):
            col = f"{base}_{idx}"
            idx += 1
        used_cols[ent.path].add(col)
        colname_by_field[f.column] = col

        parts = _parts(f.xpath)
        if from_document or ent.kind == "DOCUMENT":
            rel = parts[len(root_parts):]
        else:
            rel = parts[len(_parts(ent.path)):]
        attr = rel[-1][1:] if rel and rel[-1].startswith("@") else None
        element_parts = rel[:-1] if attr is not None else rel
        ent.columns.append(
            EntityColumn(name=col, field=f, element_parts=element_parts, attribute=attr, from_document=from_document)
        )

    top_entity = by_path[top_level[0]] if fold_document else None
    for f in fields:
        if f.flatten_path:
            add_column(by_path[f.flatten_path], f, False)
        elif fold_document and top_entity is not None:
            add_column(top_entity, f, True)
        else:
            add_column(by_path[root_path], f, False)

    for ent in entities:
        primary = ent is entities[0]
        ent.stage_table = mapping.targets.staging_table if primary else f"staging_{ds}_{ent.name}"
        ent.curated_table = mapping.targets.curated_table if primary else f"curated_{ds}_{ent.name}"

    # Business keys of the primary root entity only (child business keys are meaningless for SCD partitioning)
    primary_ent = entities[0]
    primary_ent.business_keys = [
        colname_by_field[b]
        for b in mapping.business_keys
        if b in colname_by_field and any(c.field.column == b and not c.from_document for c in primary_ent.columns)
    ]
    return EntityModel(dataset=ds, root_path=root_path, entities=entities)


def _er_type(sf_type: str) -> str:
    return re.sub(r"\(.*\)", "", sf_type).strip() or "VARCHAR"


def render_er_diagram(model: EntityModel, layer: Literal["STAGE", "GOLD"], max_columns: int = 14) -> str:
    """Mermaid `erDiagram` source of the parent/child tables of a layer."""
    lines = ["erDiagram"]

    def table(e: Entity) -> str:
        return e.stage_table if layer == "STAGE" else e.curated_table

    for e in model.entities:
        lines.append(f"    {table(e)} {{")
        lines.append(f"        VARCHAR {e.pk_column} PK")
        if e.fk_column:
            lines.append(f"        VARCHAR {e.fk_column} FK")
        shown = e.columns[:max_columns]
        for c in shown:
            lines.append(f"        {_er_type(c.field.snowflake_type)} {c.name}")
        if len(e.columns) > len(shown):
            lines.append(f'        VARCHAR _more_columns "+{len(e.columns) - len(shown)} more"')
        lines.append("    }")
    for e in model.entities:
        if e.parent is not None:
            lines.append(f'    {table(e.parent)} ||--o{{ {table(e)} : "{e.fk_column}"')
    return "\n".join(lines)
