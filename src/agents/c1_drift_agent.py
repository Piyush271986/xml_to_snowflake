"""Control Plane — C1: Drift Detection Agent.

Compares incoming XML files (and unknown XPaths surfaced at G2) against C4 mapping.yaml
and classifies each finding as ADDITIVE or BREAKING per the Change Policy.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from src.models import DatasetMapping, DriftFinding
from src.xml_infer import (
    extract_xml_xpaths_and_values,
    is_value_compatible_with_snowflake_type,
    resolve_narrowest_snowflake_type,
)


def detect_schema_drift(xml_file: Path, registry_root: Path, dataset: str) -> list[DriftFinding]:
    """Compare an XML file against C4 mapping.yaml and return all ADDITIVE and BREAKING drift findings."""
    ds_registry = registry_root / dataset
    mapping = DatasetMapping.model_validate(
        yaml.safe_load((ds_registry / "mapping.yaml").read_text(encoding="utf-8"))
    )

    xml_text = xml_file.read_text(encoding="utf-8")
    try:
        _, observed = extract_xml_xpaths_and_values(xml_text)
    except Exception:
        # Malformed XML syntax error is caught and quarantined downstream by Gate G1
        return []
    known_by_xpath = {f.xpath: f for f in mapping.fields}
    findings: list[DriftFinding] = []

    # 1. Check for new unknown XPaths
    for xp, vals in sorted(observed.items()):
        if xp not in known_by_xpath:
            inferred_sf_type = resolve_narrowest_snowflake_type(vals)
            findings.append(
                DriftFinding(
                    xpath=xp,
                    change_type="NEW_OPTIONAL_ELEMENT",
                    classification="ADDITIVE",
                    observed_type=inferred_sf_type,
                    expected_type=None,
                    sample_value=vals[0] if vals else None,
                    source_file=xml_file.name,
                )
            )

    # 2. Check for missing required XPaths (breaking)
    for xp, field_map in known_by_xpath.items():
        if field_map.required and (xp not in observed or not any(observed[xp])):
            findings.append(
                DriftFinding(
                    xpath=xp,
                    change_type="MISSING_REQUIRED_ELEMENT",
                    classification="BREAKING",
                    observed_type=None,
                    expected_type=field_map.snowflake_type,
                    sample_value=None,
                    source_file=xml_file.name,
                )
            )

    # 3. Check for incompatible data types on known XPaths (breaking)
    for xp, vals in sorted(observed.items()):
        if xp in known_by_xpath:
            expected_type = known_by_xpath[xp].snowflake_type
            for v in vals:
                if not is_value_compatible_with_snowflake_type(v, expected_type):
                    findings.append(
                        DriftFinding(
                            xpath=xp,
                            change_type="TYPE_INCOMPATIBLE",
                            classification="BREAKING",
                            observed_type=resolve_narrowest_snowflake_type([v]),
                            expected_type=expected_type,
                            sample_value=v,
                            source_file=xml_file.name,
                        )
                    )
                    break

    return findings
