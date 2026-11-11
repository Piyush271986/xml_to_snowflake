"""Unified CI/CD Pipeline Checks & Quality Certification Script.

Runs all quality gates, regression tests, cardinality audits, reconciliation checks,
and DataHub assertion publishing in a single automated command.
"""
from __future__ import annotations

import argparse
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.hierarchical_dq import audit_xml_hierarchical_integrity
from src.reconciliation_auditor import run_reconciliation_audit
from src.emit_datahub_assertions import emit_analytics_assertions


def run_all_pipeline_checks(dataset: str = "analytics") -> bool:
    print(f"================================================================================")
    print(f"  ENTERPRISE XML-TO-SNOWFLAKE PIPELINE QUALITY CERTIFICATION: {dataset.upper()}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"================================================================================\n")

    registry_dir = BASE_DIR / "registry" / dataset
    sample_file = BASE_DIR / "samples" / dataset / f"{dataset}.xml"

    if not sample_file.exists():
        print(f"❌ ERROR: Sample XML feed not found at {sample_file}")
        return False

    success = True

    # -------------------------------------------------------------------------
    # STEP 1: Deep Hierarchical DQ & Cardinality Audit
    # -------------------------------------------------------------------------
    print("👉 [1/4] Running Deep Hierarchical DQ & Cardinality Audit...")
    audit_res = audit_xml_hierarchical_integrity(sample_file)
    print(f"   • Total Assets: {audit_res['total_assets']:,}")
    print(f"   • Exploded CUSIP2 Records: {audit_res['total_cusip2_records']:,} (Avg {audit_res['average_cusip2_per_asset']}/asset)")
    print(f"   • Exploded Country Classifications: {audit_res['total_country_classifications']:,} (Avg {audit_res['average_cc_per_asset']}/asset)")
    print(f"   • Exploded CUSIP Aliases: {audit_res['total_cusip_aliases']:,}")
    print(f"   • Container SIZE Discrepancies: {audit_res['size_discrepancies']}")
    if audit_res["size_discrepancies"] == 0 and audit_res["passed"]:
        print("   ✅ PASS: Zero cardinality discrepancies detected.\n")
    else:
        print("   ❌ FAIL: Cardinality discrepancies detected!\n")
        success = False

    # -------------------------------------------------------------------------
    # STEP 2: Zero-Loss Data Reconciliation Balance Check
    # -------------------------------------------------------------------------
    print("👉 [2/4] Running Zero-Loss Data Reconciliation Balance Audit...")
    recon_res = run_reconciliation_audit(dataset, sample_file, BASE_DIR / "registry")
    metrics = recon_res["metrics"]
    print(f"   • Source Records: {metrics['source_assets']}")
    print(f"   • Curated Golden Records: {metrics['curated_assets']}")
    print(f"   • Quarantined Records: {metrics['quarantined_assets']}")
    print(f"   • Balance Discrepancy Delta: {metrics['discrepancy_delta']}")
    if recon_res["reconciliation_matched"]:
        print("   ✅ PASS: Exact 100% Zero-Loss Reconciliation Match.\n")
    else:
        print(f"   ❌ FAIL: Reconciliation mismatch (delta = {metrics['discrepancy_delta']})\n")
        success = False

    # -------------------------------------------------------------------------
    # STEP 3: Regression & Referential Integrity Test Suite
    # -------------------------------------------------------------------------
    print("👉 [3/4] Running Automated Regression & Unit Test Suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(str(BASE_DIR / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=1)
    test_result = runner.run(suite)
    if test_result.wasSuccessful():
        print(f"   ✅ PASS: All {test_result.testsRun} tests passed successfully.\n")
    else:
        print(f"   ❌ FAIL: {len(test_result.failures)} test failures, {len(test_result.errors)} errors.\n")
        success = False

    # -------------------------------------------------------------------------
    # STEP 4: Live DataHub Governance Assertion Emission
    # -------------------------------------------------------------------------
    print("👉 [4/4] Publishing Lineage & DQ Assertions to DataHub GMS...")
    try:
        dh_res = emit_analytics_assertions("http://localhost:8080", sample_file)
        print(f"   • DataHub GMS Server: http://localhost:8080")
        print(f"   • Target Dataset URN: {dh_res['dataset_urn']}")
        print(f"   • Quality Tags Emitted: {dh_res['emitted_tags']}")
        print("   ✅ PASS: Quality metadata registered in DataHub catalog.\n")
    except Exception as e:
        print(f"   ⚠️ WARNING: DataHub GMS emission skipped or unavailable: {e}\n")

    # -------------------------------------------------------------------------
    # FINAL CERTIFICATION SUMMARY
    # -------------------------------------------------------------------------
    print(f"================================================================================")
    if success:
        print("  🎉 PIPELINE CERTIFICATION: PASSED (All Quality & Regression Gates Satisfied)")
    else:
        print("  ⚠️ PIPELINE CERTIFICATION: FAILED (Review logged failures above)")
    print(f"================================================================================")

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Certification Runner")
    parser.add_argument("--dataset", default="analytics")
    args = parser.parse_args()

    ok = run_all_pipeline_checks(args.dataset)
    sys.exit(0 if ok else 1)
