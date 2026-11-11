"""Prometheus / OpenTelemetry Metrics Collector for XML Lakehouse Pipeline.

Collects operational, data quality, and hierarchical reconciliation metrics
and formats them according to standard Prometheus text exposition format (version 0.0.4).
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

from src.hierarchical_dq import audit_xml_hierarchical_integrity
from src.reconciliation_auditor import run_reconciliation_audit


def collect_pipeline_metrics(dataset: str = "analytics", registry_root: Path | None = None) -> dict[str, Any]:
    """Collects structured numeric metrics across the pipeline layers for a given dataset."""
    if registry_root is None:
        registry_root = Path("registry")

    ds_dir = registry_root / dataset
    db_path = ds_dir / "local_warehouse.db"

    # 1. Warehouse counts
    row_counts = {
        "raw": 0,
        "staging": 0,
        "curated": 0,
        "quarantine": 0,
        "dq_results": 0,
    }

    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                for layer in ["raw", "staging", "curated", "quarantine", "dq_results"]:
                    tbl = f"{layer}_{dataset}"
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                        row_counts[layer] = cursor.fetchone()[0]
                    except Exception:
                        pass
        except Exception:
            pass

    # 2. Hierarchical cardinality audit
    sample_xml = Path("samples/analytics/analytics.xml")
    if not sample_xml.exists():
        sample_xml = Path("datasets/analytics/samples/analytics.xml")

    audit = audit_xml_hierarchical_integrity(sample_xml) if sample_xml.exists() else {}

    # 3. Zero-loss reconciliation audit
    recon = run_reconciliation_audit(dataset, sample_xml, registry_root) if sample_xml.exists() else {}
    recon_metrics = recon.get("metrics", {})

    return {
        "dataset": dataset,
        "timestamp": int(time.time()),
        "warehouse_rows": row_counts,
        "source_assets": audit.get("total_assets", 0),
        "cusip2_records": audit.get("total_cusip2_records", 0),
        "country_classification_records": audit.get("total_country_classifications", 0),
        "cusip_alias_records": audit.get("total_cusip_aliases", 0),
        "size_discrepancies": audit.get("size_discrepancies", 0),
        "curated_assets": recon_metrics.get("curated_assets", row_counts["curated"]),
        "quarantined_assets": recon_metrics.get("quarantined_assets", row_counts["quarantine"]),
        "reconciliation_delta": recon_metrics.get("discrepancy_delta", 0),
        "reconciliation_matched": 1 if recon.get("reconciliation_matched", False) else 0,
    }


def format_prometheus_metrics(metrics: dict[str, Any]) -> str:
    """Formats collected pipeline metrics into standard Prometheus plain-text exposition."""
    ds = metrics["dataset"]
    lines = [
        "# HELP xml_pipeline_source_records_total Total number of source XML asset records parsed",
        "# TYPE xml_pipeline_source_records_total gauge",
        f'xml_pipeline_source_records_total{{dataset="{ds}"}} {metrics["source_assets"]}',
        "",
        "# HELP xml_pipeline_curated_records_total Total golden curated records loaded into the warehouse",
        "# TYPE xml_pipeline_curated_records_total gauge",
        f'xml_pipeline_curated_records_total{{dataset="{ds}"}} {metrics["curated_assets"]}',
        "",
        "# HELP xml_pipeline_quarantine_records_total Total records quarantined due to Gate G1/G2/G3 failures",
        "# TYPE xml_pipeline_quarantine_records_total gauge",
        f'xml_pipeline_quarantine_records_total{{dataset="{ds}"}} {metrics["quarantined_assets"]}',
        "",
        "# HELP xml_pipeline_reconciliation_delta Zero-loss balance discrepancy delta (Source - (Curated + Quarantine))",
        "# TYPE xml_pipeline_reconciliation_delta gauge",
        f'xml_pipeline_reconciliation_delta{{dataset="{ds}"}} {metrics["reconciliation_delta"]}',
        "",
        "# HELP xml_pipeline_reconciliation_matched Flag indicating whether reconciliation balance matched exactly (1=True, 0=False)",
        "# TYPE xml_pipeline_reconciliation_matched gauge",
        f'xml_pipeline_reconciliation_matched{{dataset="{ds}"}} {metrics["reconciliation_matched"]}',
        "",
        "# HELP xml_pipeline_hierarchical_discrepancies_total Total child set size discrepancies against header SIZE",
        "# TYPE xml_pipeline_hierarchical_discrepancies_total gauge",
        f'xml_pipeline_hierarchical_discrepancies_total{{dataset="{ds}"}} {metrics["size_discrepancies"]}',
        "",
        "# HELP xml_pipeline_child_records_total Exploded child entities count by entity type",
        "# TYPE xml_pipeline_child_records_total gauge",
        f'xml_pipeline_child_records_total{{dataset="{ds}",entity="cusip2"}} {metrics["cusip2_records"]}',
        f'xml_pipeline_child_records_total{{dataset="{ds}",entity="country_classification"}} {metrics["country_classification_records"]}',
        f'xml_pipeline_child_records_total{{dataset="{ds}",entity="cusip_alias"}} {metrics["cusip_alias_records"]}',
        "",
        "# HELP xml_pipeline_warehouse_rows Current row count across local warehouse layers",
        "# TYPE xml_pipeline_warehouse_rows gauge",
    ]

    for layer, count in metrics["warehouse_rows"].items():
        lines.append(f'xml_pipeline_warehouse_rows{{dataset="{ds}",layer="{layer}"}} {count}')

    lines.append("")
    return "\n".join(lines)
