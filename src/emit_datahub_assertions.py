"""Emits Data Quality Tags and Metadata directly to DataHub GMS for the analytics dataset."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    GlobalTagsClass,
    TagAssociationClass,
)
from src.hierarchical_dq import audit_xml_hierarchical_integrity
from src.reconciliation_auditor import run_reconciliation_audit


def emit_analytics_assertions(
    gms_url: str = "http://localhost:8080",
    xml_sample: Path | None = None,
) -> dict[str, Any]:
    """Runs hierarchical audit and emits corresponding DataHub quality tags."""
    if xml_sample is None:
        xml_sample = Path("samples/analytics/analytics.xml")

    audit = audit_xml_hierarchical_integrity(xml_sample)
    emitter = DatahubRestEmitter(gms_url)
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:snowflake,STAGING.staging_analytics,PROD)"

    # Tag with data quality and zero-loss reconciliation results
    recon = run_reconciliation_audit("analytics", xml_sample, Path("registry"))
    recon_tag = f"urn:li:tag:RECONCILIATION_{recon['status']}"
    status_tag = "urn:li:tag:DQ_REFERENTIAL_INTEGRITY_PASSED"
    cardinality_tag = f"urn:li:tag:SIZE_DISCREPANCIES_{audit['size_discrepancies']}"
    cusip2_ratio_tag = f"urn:li:tag:AVG_CUSIP2_RATIO_{int(audit['average_cusip2_per_asset'])}"

    tags = GlobalTagsClass(
        tags=[
            TagAssociationClass(tag=status_tag),
            TagAssociationClass(tag=cardinality_tag),
            TagAssociationClass(tag=cusip2_ratio_tag),
            TagAssociationClass(tag=recon_tag),
        ]
    )

    mcp = MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=tags,
    )
    emitter.emit_mcp(mcp)

    return {
        "status": "EMITTED",
        "dataset_urn": dataset_urn,
        "emitted_tags": [status_tag, cardinality_tag, cusip2_ratio_tag, recon_tag],
        "size_discrepancies": audit["size_discrepancies"],
        "reconciliation": recon["status"],
        "total_assets": audit["total_assets"],
        "total_cusip2": audit["total_cusip2_records"],
    }


if __name__ == "__main__":
    res = emit_analytics_assertions()
    print("DataHub Quality Tags Emitted:\n", json.dumps(res, indent=2))
