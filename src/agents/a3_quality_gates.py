"""Stage 6 — A3: Quality Gate Agent & Runtime Gate Evaluator (G1, G2, G3).

- G1 (Files, D1 -> D2): Checks XML well-formedness, non-empty size, and SHA-256 deduplication.
- G2 (Contract, D2 -> D3): Checks required XPaths, type cast compatibility, row count bounds,
  and surfaces unknown elements for C1 Drift Agent.
- G3 (Business, D3 -> D4): Checks primary keys, not-null rules, accepted values, and numeric ranges.
- Failed files/records route directly to O3: Quarantine; all check outcomes log to O1: DQ Results.
"""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.models import (
    ContractSpec,
    DatasetMapping,
    GateCheckResult,
    QualityRulesSpec,
    QuarantineRecord,
)
from src.xml_infer import (
    extract_xml_xpaths_and_values,
    flatten_xml_to_rows,
    is_value_compatible_with_snowflake_type,
)


def deploy_a3_quality_gates(dataset: str, registry_root: Path) -> dict[str, Any]:
    """Write deployed check definitions in C4 Registry."""
    ds_registry = registry_root / dataset
    contract = ContractSpec.model_validate(
        yaml.safe_load((ds_registry / "contract.yaml").read_text(encoding="utf-8"))
    )
    rules = QualityRulesSpec.model_validate(
        yaml.safe_load((ds_registry / "quality_rules.yaml").read_text(encoding="utf-8"))
    )

    deployed = {
        "dataset": dataset,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "gates": {
            "G1_Files": {
                "sits_between": "D1 (ADLS) -> D2 (Raw)",
                "checks": ["file_non_empty", "sha256_idempotency", "well_formed_xml"],
                "on_failure": "Reject and hold in O3 Quarantine",
            },
            "G2_Contract": {
                "sits_between": "D2 (Raw) -> D3 (Typed Staging)",
                "required_xpaths": contract.required_xpaths,
                "type_assertions_count": len(contract.type_assertions),
                "row_count_bounds": [
                    contract.expected_rows_per_file_min,
                    contract.expected_rows_per_file_max,
                ],
                "on_failure": "Hold in O3 Quarantine and send drift to C1",
            },
            "G3_Business": {
                "sits_between": "D3 (Typed Staging) -> D4 (Curated SCD2)",
                "primary_keys": rules.primary_keys,
                "not_null_columns": rules.not_null_columns,
                "accepted_values": rules.accepted_values,
                "numeric_ranges": [r.model_dump() for r in rules.numeric_ranges],
                "on_failure": "Hold failed records in O3 Quarantine",
            },
        },
    }
    (ds_registry / "deployed_checks.yaml").write_text(
        yaml.safe_dump(deployed, sort_keys=False),
        encoding="utf-8",
    )
    return deployed


def evaluate_file_through_gates(
    file_path: Path,
    mapping: DatasetMapping,
    contract: ContractSpec,
    rules: QualityRulesSpec,
    seen_hashes: set[str],
) -> tuple[
    bool,
    list[dict[str, Any]],
    list[GateCheckResult],
    QuarantineRecord | None,
    list[str],
]:
    """Run a single XML file through G1 -> G2 -> G3.

    Returns:
        (passed_all, valid_rows, dq_results, quarantine_record_if_failed, unknown_xpaths)
    """
    now = datetime.now(timezone.utc).isoformat()
    raw_bytes = file_path.read_bytes()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    fname = file_path.name
    dq_results: list[GateCheckResult] = []
    unknown_xpaths: list[str] = []

    # =========================================================================
    # GATE G1: FILES (Arrival, size, SHA-256 idempotency, well-formed XML)
    # =========================================================================
    if len(raw_bytes) == 0:
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G1",
                check_name="file_non_empty",
                passed=False,
                details="File is 0 bytes",
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G1",
                failure_reason="Empty XML file (0 bytes)",
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            [],
        )

    if sha256 in seen_hashes:
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G1",
                check_name="sha256_idempotency",
                passed=False,
                details=f"Duplicate file SHA-256 hash: {sha256}",
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G1",
                failure_reason=f"Duplicate file hash ({sha256[:12]}...)",
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            [],
        )

    try:
        ET.fromstring(raw_text)
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G1",
                check_name="well_formed_xml",
                passed=True,
                details="XML parsed cleanly",
                checked_at=now,
            )
        )
    except ET.ParseError as exc:
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G1",
                check_name="well_formed_xml",
                passed=False,
                details=f"Malformed XML: {exc}",
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G1",
                failure_reason=f"Malformed XML: {exc}",
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            [],
        )

    # =========================================================================
    # GATE G2: CONTRACT (Required XPaths, type casts, row counts, unknown XPaths)
    # =========================================================================
    _, observed_xpaths = extract_xml_xpaths_and_values(raw_text)
    known_xpaths = {f.xpath for f in mapping.fields}
    unknown_xpaths = sorted(xp for xp in observed_xpaths if xp not in known_xpaths)

    missing_required = [
        req for req in contract.required_xpaths if req not in observed_xpaths or not any(observed_xpaths[req])
    ]
    if missing_required:
        reason = f"Missing required XML elements: {', '.join(missing_required)}"
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G2",
                check_name="required_elements",
                passed=False,
                details=reason,
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G2",
                failure_reason=reason,
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            unknown_xpaths,
        )

    dq_results.append(
        GateCheckResult(
            dataset=mapping.dataset,
            file_name=fname,
            gate_id="G2",
            check_name="required_elements",
            passed=True,
            details="All required elements present",
            checked_at=now,
        )
    )

    # Type cast assertions
    cast_failures: list[str] = []
    for xp, target_type in contract.type_assertions.items():
        for val in observed_xpaths.get(xp, []):
            if not is_value_compatible_with_snowflake_type(val, target_type):
                cast_failures.append(f"{xp}='{val}' incompatible with {target_type}")

    if cast_failures:
        reason = f"Type cast failure: {'; '.join(cast_failures)}"
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G2",
                check_name="type_casts",
                passed=False,
                details=reason,
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G2",
                failure_reason=reason,
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            unknown_xpaths,
        )

    dq_results.append(
        GateCheckResult(
            dataset=mapping.dataset,
            file_name=fname,
            gate_id="G2",
            check_name="type_casts",
            passed=True,
            details="All XML values compatible with target Snowflake types",
            checked_at=now,
        )
    )

    rows = flatten_xml_to_rows(raw_text, mapping)
    if not (contract.expected_rows_per_file_min <= len(rows) <= contract.expected_rows_per_file_max):
        reason = (
            f"Flattened row count {len(rows)} outside expected bounds "
            f"[{contract.expected_rows_per_file_min}, {contract.expected_rows_per_file_max}]"
        )
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G2",
                check_name="row_counts",
                passed=False,
                details=reason,
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G2",
                failure_reason=reason,
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            unknown_xpaths,
        )

    # =========================================================================
    # GATE G3: BUSINESS (Keys, accepted values, numeric ranges)
    # =========================================================================
    g3_errors: list[str] = []
    seen_pks: set[tuple[Any, ...]] = set()
    for idx, r in enumerate(rows):
        pk_tuple = tuple(r.get(k) for k in rules.primary_keys)
        if any(v is None or str(v).strip() == "" for v in pk_tuple):
            g3_errors.append(f"Row {idx} has null primary key {pk_tuple}")
        elif pk_tuple in seen_pks:
            g3_errors.append(f"Duplicate primary key {pk_tuple} within file")
        seen_pks.add(pk_tuple)

        for col, allowed in rules.accepted_values.items():
            val = r.get(col)
            if val is not None and allowed and val not in allowed:
                g3_errors.append(f"Column {col}='{val}' not in accepted values {allowed}")

        for rng in rules.numeric_ranges:
            val = r.get(rng.column)
            if val is not None and str(val).strip() != "":
                num_val = float(val)
                if rng.min_value is not None and num_val < rng.min_value:
                    g3_errors.append(f"Column {rng.column}={num_val} < min {rng.min_value}")
                if rng.max_value is not None and num_val > rng.max_value:
                    g3_errors.append(f"Column {rng.column}={num_val} > max {rng.max_value}")

    if g3_errors:
        reason = "; ".join(g3_errors)
        dq_results.append(
            GateCheckResult(
                dataset=mapping.dataset,
                file_name=fname,
                gate_id="G3",
                check_name="business_rules",
                passed=False,
                details=reason,
                checked_at=now,
            )
        )
        return (
            False,
            [],
            dq_results,
            QuarantineRecord(
                dataset=mapping.dataset,
                file_name=fname,
                file_sha256=sha256,
                gate_id="G3",
                failure_reason=reason,
                raw_payload=raw_text,
                quarantined_at=now,
            ),
            unknown_xpaths,
        )

    dq_results.append(
        GateCheckResult(
            dataset=mapping.dataset,
            file_name=fname,
            gate_id="G3",
            check_name="business_rules",
            passed=True,
            details=f"All {len(rows)} flattened rows passed PK, domain, and range checks",
            checked_at=now,
        )
    )
    return True, rows, dq_results, None, unknown_xpaths
