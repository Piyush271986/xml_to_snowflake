"""Stage 7 — A4: Monitoring Agent.

Configures O2 (Freshness, Volume & Quarantine alerts routed via DataHub owners),
O5 (SLA Dashboard view), and O4 (Operator Runbook entries).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.models import DatasetMapping, OnboardingManifest


def run_a4_monitoring(dataset: str, registry_root: Path) -> dict[str, Any]:
    """Generate O2 monitoring alerts, O5 SLA dashboard SQL, and O4 Operator Runbook."""
    ds_registry = registry_root / dataset
    manifest = OnboardingManifest.model_validate(
        yaml.safe_load((ds_registry / "onboarding_manifest.yaml").read_text(encoding="utf-8"))
    )
    mapping = DatasetMapping.model_validate(
        yaml.safe_load((ds_registry / "mapping.yaml").read_text(encoding="utf-8"))
    )

    monitoring_sql = f"""-- =============================================================================
-- O2 MONITORING ALERTS & O5 SLA DASHBOARD FOR DATASET: {dataset}
-- =============================================================================

-- O5: SLA Dashboard View (Latency, Volume, Quarantine & Drift Trends)
CREATE SCHEMA IF NOT EXISTS OPS;

CREATE OR REPLACE VIEW OPS.v_sla_dashboard_{dataset} AS
SELECT
    DATE_TRUNC('HOUR', r._ingestion_ts)                          AS load_hour,
    COUNT(DISTINCT r._file_name)                            AS files_ingested,
    COUNT(c._row_hash)                                      AS curated_active_rows,
    AVG(DATEDIFF('SECOND', r._ingestion_ts, c.valid_start_time)) AS avg_e2e_latency_sec,
    (SELECT COUNT(*) FROM OPS.{mapping.targets.quarantine_table} q WHERE q.replayed = FALSE) AS open_quarantine_count
FROM RAW.{mapping.targets.raw_table} r
LEFT JOIN CURATED.{mapping.targets.curated_table} c
  ON c._source_file = r._file_name AND c.is_current = TRUE
GROUP BY 1;

-- O2: Freshness Alert Check (fires if no new files within {manifest.freshness_sla_hours}h SLA)
SELECT
    '{dataset}' AS dataset,
    DATEDIFF('HOUR', MAX(_ingestion_ts), CURRENT_TIMESTAMP()) AS hours_since_last_load,
    '{manifest.platform_oncall}' AS alert_owner
FROM RAW.{mapping.targets.raw_table}
HAVING hours_since_last_load > {manifest.freshness_sla_hours};
"""
    (ds_registry / "monitoring.sql").write_text(monitoring_sql, encoding="utf-8")

    runbook_entries = [
        {
            "signal": "File fails G1 checks",
            "meaning": "Malformed XML or a duplicate file",
            "first_action": f"Open O3 ({mapping.targets.quarantine_table}), fix the source file, then replay",
            "owner": manifest.engineering_owner,
        },
        {
            "signal": "Additive drift flagged by C1",
            "meaning": "New optional XML element found",
            "first_action": "Auto-applied to mapping.yaml & DDL. Review in the weekly drift report",
            "owner": manifest.data_steward,
        },
        {
            "signal": "Breaking drift flagged by C1",
            "meaning": "Element renamed, removed, or retyped",
            "first_action": "Review the C2 proposal at C3, then approve or reject",
            "owner": manifest.data_steward,
        },
        {
            "signal": "Load is late (O2 alert)",
            "meaning": f"No new files within {manifest.freshness_sla_hours}h, or pipe_{dataset} is paused",
            "first_action": f"Check D1 ({manifest.adls_landing_path}) for new files, then resume pipe_{dataset}",
            "owner": manifest.platform_oncall,
        },
        {
            "signal": "Row counts differ (G2 alert)",
            "meaning": "Flattening dropped records",
            "first_action": f"Compare D2 ({mapping.targets.raw_table}) and D3 ({mapping.targets.staging_table}), fix mapping, replay",
            "owner": manifest.engineering_owner,
        },
        {
            "signal": "Records fail G2 or G3 checks",
            "meaning": "Missing element, bad type, or broken key",
            "first_action": f"Open O3 ({mapping.targets.quarantine_table}) for the reason, fix mapping or source, then replay",
            "owner": manifest.engineering_owner,
        },
    ]

    monitoring_config = {
        "dataset": dataset,
        "configured_at": datetime.now(timezone.utc).isoformat(),
        "o2_alerts": {
            "freshness_sla_hours": manifest.freshness_sla_hours,
            "quarantine_threshold": 0,
            "routing_source": "DataHub_Owner_Lookup",
        },
        "o5_sla_dashboard_view": f"v_sla_dashboard_{dataset}",
        "o4_operator_runbook": runbook_entries,
    }
    (ds_registry / "monitoring_config.yaml").write_text(
        yaml.safe_dump(monitoring_config, sort_keys=False),
        encoding="utf-8",
    )
    return monitoring_config
