"""Audits live Snowflake objects, row counts, dynamic table refresh states, and foreign key integrity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.snowflake_client import (
    connect_snowflake_external_browser,
    get_snowflake_status,
    load_snowflake_config,
)


def audit_live_snowflake() -> dict[str, Any]:
    print("================================================================================")
    print("  SNOWFLAKE LIVE OBJECT & REFERENTIAL INTEGRITY AUDITOR")
    print("================================================================================\n")

    cfg = load_snowflake_config()
    status = get_snowflake_status()

    if not cfg.is_configured:
        print("ℹ️ Snowflake connection settings in config/settings.yaml are unpopulated.")
        print("👉 Running Local Warehouse Audit (SQLite Mirror: registry/analytics/local_warehouse.db)...\n")
        db_path = BASE_DIR / "registry" / "analytics" / "local_warehouse.db"
        if db_path.exists():
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(db_path)) as conn:
                cur = conn.cursor()
                print("👉 Table Row Counts (Local Warehouse):")
                for tbl in ["raw_analytics", "staging_analytics", "curated_analytics", "quarantine_analytics"]:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                        cnt = cur.fetchone()[0]
                        print(f"   • {tbl:<45} : {cnt:,} rows")
                    except sqlite3.Error as e:
                        print(f"   • {tbl:<45} : NOT FOUND ({e})")
        print("\n================================================================================")
        print("  🎉 LOCAL WAREHOUSE AUDIT COMPLETED")
        print("================================================================================")
        return {"mode": "local_simulation", "configured": False}

    print(f"👉 Account: {cfg.account}")
    print(f"👉 Database: {cfg.database} | Warehouse: {cfg.warehouse} | Role: {cfg.role}")
    print(f"👉 Authenticator: {cfg.authenticator}\n")

    tables_to_check = [
        ("RAW", "RAW_ANALYTICS"),
        ("STAGING", "STAGING_ANALYTICS"),
        ("STAGING", "STAGING_ANALYTICS_CUSIP2"),
        ("STAGING", "STAGING_ANALYTICS_COUNTRY_CLASSIFICATION"),
        ("STAGING", "STAGING_ANALYTICS_CUSIP_ALIAS"),
        ("CURATED", "CURATED_ANALYTICS"),
        ("CURATED", "CURATED_ANALYTICS_CUSIP2"),
        ("CURATED", "CURATED_ANALYTICS_COUNTRY_CLASSIFICATION"),
        ("CURATED", "CURATED_ANALYTICS_CUSIP_ALIAS"),
        ("OPS", "QUARANTINE_ANALYTICS"),
    ]

    results: dict[str, Any] = {
        "account": cfg.account,
        "database": cfg.database,
        "tables": {},
    }

    try:
        conn = connect_snowflake_external_browser(cfg)
        with conn.cursor() as cur:
            # 1. Row counts
            print("👉 Table Row Counts:")
            for schema, tbl in tables_to_check:
                full_name = f"{cfg.database}.{schema}.{tbl}"
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {full_name};")
                    cnt = cur.fetchone()[0]
                    results["tables"][full_name] = cnt
                    print(f"   • {full_name:<55} : {cnt:,} rows")
                except Exception as e:
                    results["tables"][full_name] = f"ERROR ({e})"
                    print(f"   • {full_name:<55} : NOT FOUND / ERROR")

            # 2. Dynamic Table Refresh States
            print("\n👉 Dynamic Table Scheduling States (STAGING):")
            try:
                cur.execute(f"SHOW DYNAMIC TABLES IN SCHEMA {cfg.database}.STAGING;")
                for row in cur.fetchall():
                    dt_name = row[1]
                    target_lag = row[8]
                    state = row[11]
                    print(f"   • {dt_name:<40} | Lag: {target_lag:<10} | State: {state}")
            except Exception as e:
                print(f"   ⚠️ Could not inspect dynamic table states: {e}")

            # 3. Foreign key referential integrity check
            print("\n👉 Foreign Key Integrity (Orphan Validation):")
            try:
                cur.execute(f"""
                    SELECT COUNT(*)
                    FROM {cfg.database}.STAGING.STAGING_ANALYTICS_CUSIP2 c
                    LEFT JOIN {cfg.database}.STAGING.STAGING_ANALYTICS p
                      ON c.analytics_fk = p.analytics_pk
                    WHERE p.analytics_pk IS NULL;
                """)
                orphan_c2 = cur.fetchone()[0]
                print(f"   • STAGING_ANALYTICS_CUSIP2 Orphan Rows: {orphan_c2}")
                results["orphan_cusip2"] = orphan_c2
            except Exception as e:
                print(f"   ⚠️ Orphan check skipped: {e}")

        conn.close()
        print("\n================================================================================")
        print("  🎉 SNOWFLAKE AUDIT COMPLETED SUCCESSFULLY")
        print("================================================================================")
    except Exception as e:
        print(f"\n⚠️ Live Snowflake connection skipped or deferred: {e}")
        results["error"] = str(e)

    return results


if __name__ == "__main__":
    audit_live_snowflake()
