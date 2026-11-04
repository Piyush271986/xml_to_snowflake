"""Stage 4 — A1: DDL Deployment Agent.

Deploys the approved ddl.sql from C4 Registry. In local_simulation mode, provisions a local
SQLite relational mirror of raw_<dataset>, staging_<dataset>, curated_<dataset> (SCD Type 2),
quarantine_<dataset> (O3), and dq_results_<dataset> (O1).
"""
from __future__ import annotations

from contextlib import closing
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from src.models import DatasetMapping


def _sf_type_to_sqlite(sf_type: str) -> str:
    if sf_type == "NUMBER(18,0)":
        return "INTEGER"
    if sf_type.startswith("NUMBER"):
        return "REAL"
    if sf_type == "BOOLEAN":
        return "INTEGER"
    return "TEXT"


def run_a1_provision(dataset: str, registry_root: Path) -> dict[str, Any]:
    """Validate Snowflake DDL and provision local warehouse tables for testing & simulation."""
    ds_registry = registry_root / dataset
    ddl_path = ds_registry / "ddl.sql"
    mapping_path = ds_registry / "mapping.yaml"

    if not ddl_path.exists() or not mapping_path.exists():
        raise FileNotFoundError(f"A1 Provision failed: missing ddl.sql or mapping.yaml in {ds_registry}")

    mapping = DatasetMapping.model_validate(yaml.safe_load(mapping_path.read_text(encoding="utf-8")))
    db_path = ds_registry / "local_warehouse.db"
    if db_path.exists():
        db_path.unlink()

    col_defs = ",\n    ".join(
        f"{f.column} {_sf_type_to_sqlite(f.snowflake_type)}" for f in mapping.fields
    )

    with closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        # D2: Raw Layer (idempotent on _file_name + _file_sha256)
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {mapping.targets.raw_table} (
                _file_name TEXT NOT NULL,
                _file_sha256 TEXT NOT NULL,
                _source_system TEXT NOT NULL,
                _load_ts TEXT NOT NULL,
                raw_xml TEXT NOT NULL,
                UNIQUE(_file_name, _file_sha256)
            );
            """
        )

        # D3: Typed Staging
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {mapping.targets.staging_table} (
                {col_defs},
                _file_name TEXT NOT NULL,
                _file_sha256 TEXT NOT NULL,
                _staged_ts TEXT NOT NULL
            );
            """
        )

        # D4: Curated SCD Type 2
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {mapping.targets.curated_table} (
                {col_defs},
                _row_hash TEXT NOT NULL,
                is_valid_start TEXT NOT NULL,
                is_valid_end TEXT,
                is_current INTEGER NOT NULL DEFAULT 1,
                system_start_time TEXT NOT NULL,
                system_end_time TEXT,
                _source_file TEXT NOT NULL
            );
            """
        )

        # O3: Quarantine
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {mapping.targets.quarantine_table} (
                dataset TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_sha256 TEXT NOT NULL,
                gate_id TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                raw_payload TEXT NOT NULL,
                quarantined_at TEXT NOT NULL,
                replayed INTEGER NOT NULL DEFAULT 0
            );
            """
        )

        # O1: DQ Results
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {mapping.targets.dq_results_table} (
                dataset TEXT NOT NULL,
                file_name TEXT NOT NULL,
                gate_id TEXT NOT NULL,
                check_name TEXT NOT NULL,
                passed INTEGER NOT NULL,
                details TEXT NOT NULL,
                checked_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

    summary = {
        "dataset": dataset,
        "version": mapping.version,
        "snowflake_ddl_file": str(ddl_path),
        "local_warehouse_db": str(db_path),
        "provisioned_objects": [
            mapping.targets.raw_table,
            mapping.targets.staging_table,
            mapping.targets.curated_table,
            mapping.targets.quarantine_table,
            mapping.targets.dq_results_table,
            f"pipe_{dataset} (PAUSED)",
            f"stream_{mapping.targets.raw_table}",
            f"task_flatten_{dataset}",
            f"task_scd2_{dataset}",
        ],
    }
    (ds_registry / "provisioned_objects.yaml").write_text(
        yaml.safe_dump(summary, sort_keys=False),
        encoding="utf-8",
    )
    return summary
