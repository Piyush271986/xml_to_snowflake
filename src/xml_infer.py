"""Core XML XPath discovery, narrowest-type inference, cardinality detection, and record extraction."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from src.models import DatasetMapping, FieldMapping, TargetTables

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$")


def infer_single_value_type(val: str) -> str:
    """Return the narrowest type category for a single string value."""
    v = val.strip()
    if not v:
        return "EMPTY"
    if v.lower() in ("true", "false"):
        return "BOOLEAN"
    if re.match(r"^-?\d+$", v):
        try:
            int(v)
            return "INT"
        except ValueError:
            pass
    if re.match(r"^-?\d+\.\d+$", v):
        try:
            Decimal(v)
            return "DECIMAL"
        except InvalidOperation:
            pass
    if DATE_RE.match(v):
        try:
            date.fromisoformat(v)
            return "DATE"
        except ValueError:
            pass
    if TIMESTAMP_RE.match(v):
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return "TIMESTAMP_NTZ"
        except ValueError:
            pass
    return "VARCHAR"


def resolve_narrowest_snowflake_type(values: list[str]) -> str:
    """Pick the narrowest Snowflake type that fits 100% of observed non-empty values."""
    cats = {infer_single_value_type(v) for v in values if v and v.strip()}
    cats.discard("EMPTY")
    if not cats:
        return "VARCHAR"
    if cats == {"INT"}:
        return "NUMBER(18,0)"
    if cats <= {"INT", "DECIMAL"}:
        return "NUMBER(18,4)"
    if cats == {"BOOLEAN"}:
        return "BOOLEAN"
    if cats == {"DATE"}:
        return "DATE"
    if cats <= {"DATE", "TIMESTAMP_NTZ"}:
        return "TIMESTAMP_NTZ"
    return "VARCHAR"


def is_value_compatible_with_snowflake_type(val: str, sf_type: str) -> bool:
    """Check if a string value can be safely cast to the target Snowflake type."""
    if val is None or val.strip() == "":
        return True
    inferred = infer_single_value_type(val)
    if sf_type.startswith(" VARCHAR") or sf_type.startswith("VARCHAR"):
        return True
    if sf_type == "NUMBER(18,0)":
        return inferred == "INT"
    if sf_type.startswith("NUMBER"):
        return inferred in ("INT", "DECIMAL")
    if sf_type == "BOOLEAN":
        return inferred == "BOOLEAN"
    if sf_type == "DATE":
        return inferred == "DATE"
    if sf_type == "TIMESTAMP_NTZ":
        return inferred in ("DATE", "TIMESTAMP_NTZ")
    return True


def to_snake_case(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def build_column_name(xpath: str, root_tag: str, flatten_path: str | None) -> str:
    """Convert an XPath into a clean snake_case Snowflake column name."""
    parts = [p for p in xpath.strip("/").split("/") if p]
    if parts and parts[0] == root_tag:
        parts = parts[1:]
    if parts and parts[-1].startswith("@"):
        attr = to_snake_case(parts[-1][1:])
        prefix = to_snake_case(parts[-2]) if len(parts) > 1 else ""
        return f"{prefix}_{attr}".strip("_") if prefix else f"{attr}_code" if attr == "currency" else attr

    if flatten_path:
        flatten_parts = [p for p in flatten_path.strip("/").split("/") if p]
        array_node = to_snake_case(flatten_parts[-1])
        leaf_node = to_snake_case(parts[-1])
        if not leaf_node.startswith(array_node):
            return f"{array_node}_{leaf_node}"
    return to_snake_case(parts[-1])


def build_snowflake_xml_expr(
    xpath: str,
    root_tag: str,
    sf_type: str,
    is_array: bool,
    flatten_path: str | None,
    is_attribute: bool,
) -> str:
    """Generate the Snowflake SQL expression using XMLGET / TRY_CAST / LATERAL FLATTEN."""
    parts = [p for p in xpath.strip("/").split("/") if p]
    if is_attribute:
        attr_name = parts[-1]  # e.g. @currency
        return f'raw_xml:"{attr_name}"::{sf_type}'

    if is_array and flatten_path:
        flatten_parts = [p for p in flatten_path.strip("/").split("/") if p]
        rel_parts = parts[len(flatten_parts) :]
        expr = "item.value"
        for p in rel_parts:
            expr = f"XMLGET({expr}, '{p}')"
        raw_val = f'{expr}:"$"::VARCHAR'
    else:
        rel_parts = parts[1:] if parts and parts[0] == root_tag else parts
        expr = "raw_xml"
        for p in rel_parts:
            expr = f"XMLGET({expr}, '{p}')"
        raw_val = f'{expr}:"$"::VARCHAR'

    if sf_type == "NUMBER(18,0)":
        return f"TRY_TO_NUMBER({raw_val}, 18, 0)"
    if sf_type == "NUMBER(18,4)":
        return f"TRY_TO_DECIMAL({raw_val}, 18, 4)"
    if sf_type == "DATE":
        return f"TRY_TO_DATE({raw_val})"
    if sf_type == "TIMESTAMP_NTZ":
        return f"TRY_TO_TIMESTAMP_NTZ({raw_val})"
    if sf_type == "BOOLEAN":
        return f"TRY_TO_BOOLEAN({raw_val})"
    return raw_val


def infer_schema_from_xml_files(dataset: str, xml_files: list[Path]) -> DatasetMapping:
    """Parse sample XML files, union XPaths, infer types, optionality, cardinality, and confidence."""
    total_files = len(xml_files)
    if total_files == 0:
        raise ValueError("At least one valid sample XML file is required for C0 inference.")

    xpath_files_present: dict[str, set[str]] = defaultdict(set)
    xpath_values: dict[str, list[str]] = defaultdict(list)
    xpath_is_attr: dict[str, bool] = {}
    repeating_container_paths: set[str] = set()
    ordered_xpaths: list[str] = []
    root_tag: str | None = None

    def walk(elem: ET.Element, current_path: str, file_name: str) -> None:
        # Record attributes on current element
        for attr_key, attr_val in elem.attrib.items():
            attr_xpath = f"{current_path}/@{attr_key}"
            if attr_xpath not in ordered_xpaths:
                ordered_xpaths.append(attr_xpath)
            xpath_is_attr[attr_xpath] = True
            xpath_files_present[attr_xpath].add(file_name)
            xpath_values[attr_xpath].append(attr_val)

        children = list(elem)
        if not children:
            # Leaf element
            text_val = (elem.text or "").strip()
            if current_path not in ordered_xpaths:
                ordered_xpaths.append(current_path)
            xpath_is_attr[current_path] = False
            if text_val != "":
                xpath_files_present[current_path].add(file_name)
                xpath_values[current_path].append(text_val)
            return

        # Count child tag frequencies under this parent to detect arrays
        tag_counts = Counter(child.tag for child in children)
        for tag, count in tag_counts.items():
            if count > 1:
                repeating_container_paths.add(f"{current_path}/{tag}")

        for child in children:
            walk(child, f"{current_path}/{child.tag}", file_name)

    for xml_path in sorted(xml_files):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        if root_tag is None:
            root_tag = root.tag
        walk(root, f"/{root.tag}", xml_path.name)

    assert root_tag is not None
    root_element = f"/{root_tag}"

    fields: list[FieldMapping] = []
    for xpath in ordered_xpaths:
        is_attr = xpath_is_attr.get(xpath, False)
        files_seen = len(xpath_files_present[xpath])
        confidence = round(files_seen / total_files, 2)
        required = files_seen == total_files

        flatten_path: str | None = None
        for rep_path in sorted(repeating_container_paths, key=len, reverse=True):
            if xpath.startswith(rep_path + "/") or xpath == rep_path:
                flatten_path = rep_path
                break
        is_array = flatten_path is not None

        values = xpath_values[xpath]
        sf_type = resolve_narrowest_snowflake_type(values)
        col_name = build_column_name(xpath, root_tag, flatten_path)
        xml_expr = build_snowflake_xml_expr(
            xpath=xpath,
            root_tag=root_tag,
            sf_type=sf_type,
            is_array=is_array,
            flatten_path=flatten_path,
            is_attribute=is_attr,
        )

        # Deduplicate sample preview values (up to 20 distinct values for domain inference)
        sample_vals: list[str] = []
        for v in values:
            if v not in sample_vals:
                sample_vals.append(v)
            if len(sample_vals) >= 20:
                break

        fields.append(
            FieldMapping(
                xpath=xpath,
                column=col_name,
                snowflake_type=sf_type,
                xml_expr=xml_expr,
                required=required,
                is_array=is_array,
                flatten_path=flatten_path,
                is_attribute=is_attr,
                confidence=confidence,
                sample_values=sample_vals,
                origin="c0_bootstrap",
                added_in_version="0.1.0",
            )
        )

    # Identify business keys: required ID fields at root level (+ first array code if array exists)
    business_keys: list[str] = []
    for f in fields:
        if not f.is_array and f.required and f.column.endswith("_id"):
            business_keys.append(f.column)
            break
    if not business_keys and fields:
        business_keys.append(fields[0].column)
    # If there is an array grain, include the first array identifier in the staging/curated grain key
    for f in fields:
        if f.is_array and ("code" in f.column or "id" in f.column):
            business_keys.append(f.column)
            break

    return DatasetMapping(
        dataset=dataset,
        version="0.1.0",
        source="sample_inference",
        root_element=root_element,
        business_keys=business_keys,
        targets=TargetTables(
            raw_table=f"raw_{dataset}",
            staging_table=f"staging_{dataset}",
            curated_table=f"curated_{dataset}",
            quarantine_table=f"quarantine_{dataset}",
            dq_results_table=f"dq_results_{dataset}",
        ),
        fields=fields,
    )


def extract_xml_xpaths_and_values(xml_text: str) -> tuple[str, dict[str, list[str]]]:
    """Return root_element and all leaf/attribute XPaths -> list of observed string values in a single XML."""
    root = ET.fromstring(xml_text)
    observed: dict[str, list[str]] = defaultdict(list)

    def walk(elem: ET.Element, current_path: str) -> None:
        for attr_key, attr_val in elem.attrib.items():
            observed[f"{current_path}/@{attr_key}"].append(attr_val)
        children = list(elem)
        if not children:
            observed[current_path].append((elem.text or "").strip())
            return
        for child in children:
            walk(child, f"{current_path}/{child.tag}")

    walk(root, f"/{root.tag}")
    return f"/{root.tag}", dict(observed)


def flatten_xml_to_rows(xml_text: str, mapping: DatasetMapping) -> list[dict[str, Any]]:
    """Flatten an XML document into typed staging rows matching Snowflake's LATERAL FLATTEN semantics."""
    root = ET.fromstring(xml_text)
    root_prefix = mapping.root_element.strip("/")

    scalar_fields = [f for f in mapping.fields if not f.is_array]
    array_fields = [f for f in mapping.fields if f.is_array]

    base_row: dict[str, Any] = {}
    for sf in scalar_fields:
        parts = [p for p in sf.xpath.strip("/").split("/") if p]
        rel_parts = parts[1:] if parts and parts[0] == root_prefix else parts
        if sf.is_attribute:
            attr_name = rel_parts[-1][1:]
            node = root
            for p in rel_parts[:-1]:
                node = node.find(p) if node is not None else None
            base_row[sf.column] = node.attrib.get(attr_name) if node is not None else None
        else:
            node = root
            for p in rel_parts:
                node = node.find(p) if node is not None else None
            base_row[sf.column] = (node.text or "").strip() if (node is not None and node.text) else None

    if not array_fields:
        return [base_row]

    # Group by flatten_path (e.g. /Order/LineItems/LineItem)
    flatten_path = array_fields[0].flatten_path
    assert flatten_path is not None
    fp_parts = [p for p in flatten_path.strip("/").split("/") if p]
    rel_fp = "/".join(fp_parts[1:]) if fp_parts[0] == root_prefix else "/".join(fp_parts)
    array_nodes = root.findall(rel_fp)
    if not array_nodes:
        row = dict(base_row)
        for af in array_fields:
            row[af.column] = None
        return [row]

    rows: list[dict[str, Any]] = []
    for item_elem in array_nodes:
        row = dict(base_row)
        for af in array_fields:
            af_parts = [p for p in af.xpath.strip("/").split("/") if p]
            rel_item_parts = af_parts[len(fp_parts) :]
            sub = item_elem
            for p in rel_item_parts:
                sub = sub.find(p) if sub is not None else None
            row[af.column] = (sub.text or "").strip() if (sub is not None and sub.text) else None
        rows.append(row)
    return rows
