"""Stage 8 — A5: Smoke Test Agent.

Loads all sample XMLs through G1 -> D2 (Raw) -> G2 -> D3 (Typed Staging) -> G3 -> D4 (Curated SCD Type 2),
verifies quarantine_<dataset> is empty, and produces smoke_test_report.md for Stage 9 Go-Live.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.agents.a3_quality_gates import evaluate_file_through_gates
from src.models import (
    ContractSpec,
    DatasetMapping,
    OnboardingManifest,
    QualityRulesSpec,
)


def ingest_xml_files_into_warehouse(
    xml_files: list[Path],
    ds_registry: Path,
) -> dict[str, Any]:
    """Process a batch of XML files through G1/G2/G3 into D2, D3, D4 (SCD Type 2), O1, and O3."""
    mapping = DatasetMapping.model_validate(
        yaml.safe_load((ds_registry / "mapping.yaml").read_text(encoding="utf-8"))
    )
    contract = ContractSpec.model_validate(
        yaml.safe_load((ds_registry / "contract.yaml").read_text(encoding="utf-8"))
    )
    rules = QualityRulesSpec.model_validate(
        yaml.safe_load((ds_registry / "quality_rules.yaml").read_text(encoding="utf-8"))
    )
    db_path = ds_registry / "local_warehouse.db"

    field_cols = [f.column for f in mapping.fields]
    non_key_cols = [c for c in field_cols if c not in mapping.business_keys]

    files_passed = 0
    files_quarantined = 0
    total_staged_rows = 0
    all_unknown_xpaths: set[str] = set()

    with closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT _file_sha256 FROM {mapping.targets.raw_table}")
        seen_hashes: set[str] = {r[0] for r in cur.fetchall()}

        for xml_path in xml_files:
            now = datetime.now(timezone.utc).isoformat()
            raw_bytes = xml_path.read_bytes()
            raw_text = raw_bytes.decode("utf-8", errors="replace")
            file_sha256 = hashlib.sha256(raw_bytes).hexdigest()

            passed, rows, dq_results, quarantine_rec, unknown_xpaths = evaluate_file_through_gates(
                file_path=xml_path,
                mapping=mapping,
                contract=contract,
                rules=rules,
                seen_hashes=seen_hashes,
            )
            all_unknown_xpaths.update(unknown_xpaths)

            # Log every check to O1: DQ Results
            for dq in dq_results:
                cur.execute(
                    f"""
                    INSERT INTO {mapping.targets.dq_results_table}
                    (dataset, file_name, gate_id, check_name, passed, details, checked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dq.dataset,
                        dq.file_name,
                        dq.gate_id,
                        dq.check_name,
                        1 if dq.passed else 0,
                        dq.details,
                        dq.checked_at,
                    ),
                )

            if not passed and quarantine_rec is not None:
                files_quarantined += 1
                cur.execute(
                    f"""
                    INSERT INTO {mapping.targets.quarantine_table}
                    (dataset, file_name, file_sha256, gate_id, failure_reason, raw_payload, quarantined_at, replayed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        quarantine_rec.dataset,
                        quarantine_rec.file_name,
                        quarantine_rec.file_sha256,
                        quarantine_rec.gate_id,
                        quarantine_rec.failure_reason,
                        quarantine_rec.raw_payload,
                        quarantine_rec.quarantined_at,
                    ),
                )
                continue

            # File passed G1, G2, G3 -> Load D2 Raw, D3 Staging, and D4 Curated (SCD Type 2)
            files_passed += 1
            seen_hashes.add(file_sha256)

            cur.execute(
                f"""
                INSERT INTO {mapping.targets.raw_table}
                (_file_name, _file_sha256, _source_system, _load_ts, raw_xml)
                VALUES (?, ?, ?, ?, ?)
                """,
                (xml_path.name, file_sha256, mapping.dataset, now, raw_text),
            )

            col_names_sql = ", ".join(field_cols)
            placeholders_sql = ", ".join("?" for _ in field_cols)

            for r in rows:
                total_staged_rows += 1
                vals = [r.get(c) for c in field_cols]
                cur.execute(
                    f"""
                    INSERT INTO {mapping.targets.staging_table}
                    ({col_names_sql}, _file_name, _file_sha256, _staged_ts)
                    VALUES ({placeholders_sql}, ?, ?, ?)
                    """,
                    (*vals, xml_path.name, file_sha256, now),
                )

                # SCD Type 2 logic into Curated table
                row_hash_input = "|".join(str(r.get(c) or "") for c in non_key_cols)
                row_hash = hashlib.sha256(row_hash_input.encode("utf-8")).hexdigest()

                where_bk = " AND ".join(f"{k} = ?" for k in mapping.business_keys)
                bk_vals = [str(r.get(k)) for k in mapping.business_keys]

                cur.execute(
                    f"""
                    SELECT _row_hash FROM {mapping.targets.curated_table}
                    WHERE {where_bk} AND is_current = 1
                    """,
                    bk_vals,
                )
                existing = cur.fetchone()
                if existing is not None:
                    if existing[0] == row_hash:
                        # Unchanged record — idempotent skip
                        continue
                    # Close current SCD2 version
                    cur.execute(
                        f"""
                        UPDATE {mapping.targets.curated_table}
                        SET is_valid_end = ?, is_current = 0, system_end_time = ?
                        WHERE {where_bk} AND is_current = 1
                        """,
                        (now, now, *bk_vals),
                    )

                cur.execute(
                    f"""
                    INSERT INTO {mapping.targets.curated_table}
                    ({col_names_sql}, _row_hash, is_valid_start, is_valid_end, is_current, system_start_time, system_end_time, _source_file)
                    VALUES ({placeholders_sql}, ?, ?, NULL, 1, ?, NULL, ?)
                    """,
                    (*vals, row_hash, now, now, xml_path.name),
                )

        conn.commit()

        cur.execute(f"SELECT COUNT(*) FROM {mapping.targets.raw_table}")
        raw_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {mapping.targets.staging_table}")
        staging_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {mapping.targets.curated_table} WHERE is_current = 1")
        curated_current_count = cur.fetchone()[0]
        cur.execute(f"SELECT COUNT(*) FROM {mapping.targets.quarantine_table} WHERE replayed = 0")
        quarantine_count = cur.fetchone()[0]

    return {
        "files_processed": len(xml_files),
        "files_passed": files_passed,
        "files_quarantined": files_quarantined,
        "raw_table_rows": raw_count,
        "staging_table_rows": staging_count,
        "curated_current_rows": curated_current_count,
        "quarantine_open_rows": quarantine_count,
        "unknown_xpaths": sorted(all_unknown_xpaths),
    }


def run_a5_smoke_test(dataset: str, registry_root: Path) -> dict[str, Any]:
    """Run all onboarding sample XMLs end-to-end and write smoke_test_report.md."""
    ds_registry = registry_root / dataset
    manifest = OnboardingManifest.model_validate(
        yaml.safe_load((ds_registry / "onboarding_manifest.yaml").read_text(encoding="utf-8"))
    )
    sample_dir = Path(manifest.onboarding_sample_dir)
    xml_files = [sample_dir / fname for fname in manifest.valid_sample_files]

    metrics = ingest_xml_files_into_warehouse(xml_files, ds_registry)
    smoke_passed = metrics["quarantine_open_rows"] == 0 and metrics["files_passed"] == len(xml_files)
    metrics["smoke_test_passed"] = smoke_passed

    status_badge = "✅ PASSED" if smoke_passed else "❌ FAILED"
    report_lines = [
        f"# A5 Smoke Test Report — `{dataset}` ({status_badge})",
        "",
        f"- **Executed At:** `{datetime.now(timezone.utc).isoformat()}`",
        f"- **Sample XMLs Tested:** {metrics['files_processed']}",
        f"- **Files Passed (G1 + G2 + G3):** {metrics['files_passed']}",
        f"- **D2 Raw Rows (`raw_{dataset}`):** {metrics['raw_table_rows']}",
        f"- **D3 Staging Rows (`staging_{dataset}`):** {metrics['staging_table_rows']}",
        f"- **D4 Curated Active SCD2 Rows (`curated_{dataset}`):** {metrics['curated_current_rows']}",
        f"- **O3 Quarantine Count (`quarantine_{dataset}`):** {metrics['quarantine_open_rows']} *(must be 0)*",
        "",
        "## Gate Verification Summary",
        "",
        "| Gate | Check Scope | Result |",
        "|---|---|---|",
        f"| **G1: Files** | Arrival, SHA-256 idempotency, XML well-formedness | {'✅ PASS' if smoke_passed else '❌ FAIL'} |",
        f"| **G2: Contract** | Required XPaths, type casts, flattened row counts | {'✅ PASS' if smoke_passed else '❌ FAIL'} |",
        f"| **G3: Business** | Primary keys (`order_id`, `line_item_product_code`), ranges, domains | {'✅ PASS' if smoke_passed else '❌ FAIL'} |",
    ]
    (ds_registry / "smoke_test_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return metrics
