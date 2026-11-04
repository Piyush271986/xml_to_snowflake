"""End-to-End Orchestrator for XML Dataset Onboarding (Stages 1-10) and Runtime Drift Control."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from src.agents.a0_intake import run_a0_intake
from src.agents.a1_provision import run_a1_provision
from src.agents.a2_catalog import run_a2_catalog
from src.agents.a3_quality_gates import deploy_a3_quality_gates
from src.agents.a4_monitoring import run_a4_monitoring
from src.agents.a5_smoke_test import ingest_xml_files_into_warehouse, run_a5_smoke_test
from src.agents.c0_bootstrap import run_c0_bootstrap
from src.agents.c1_drift_agent import detect_schema_drift
from src.agents.c2_proposal_agent import handle_drift_findings
from src.models import OnboardingManifest


def approve_c3_schema_review(dataset: str, registry_root: Path) -> None:
    """Stage 3 — C3: Data Steward approves inferred mapping.yaml and contract.yaml."""
    ds_registry = registry_root / dataset
    manifest_path = ds_registry / "onboarding_manifest.yaml"
    manifest = OnboardingManifest.model_validate(
        yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    )
    manifest.status = "APPROVED"
    manifest_path.write_text(
        yaml.safe_dump(manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )


def approve_c3_go_live(dataset: str, registry_root: Path) -> dict[str, Any]:
    """Stage 9 & 10 — C3 Go-Live Gate: Engineering approves smoke test & enables production Snowpipe."""
    ds_registry = registry_root / dataset
    manifest_path = ds_registry / "onboarding_manifest.yaml"
    manifest = OnboardingManifest.model_validate(
        yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    )
    manifest.status = "PUBLISHED"
    manifest_path.write_text(
        yaml.safe_dump(manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    dh_path = ds_registry / "datahub_urns.yaml"
    if dh_path.exists():
        dh = yaml.safe_load(dh_path.read_text(encoding="utf-8"))
        dh["status"] = "PUBLISHED"
        dh["git_tag"] = "v1.0.0-live"
        dh["snowpipe_state"] = "ACTIVE"
        dh_path.write_text(yaml.safe_dump(dh, sort_keys=False), encoding="utf-8")

    return {
        "dataset": dataset,
        "status": "PUBLISHED",
        "git_tag": "v1.0.0-live",
        "snowpipe_sql": f"ALTER PIPE pipe_{dataset} SET PIPE_EXECUTION_PAUSED = FALSE;",
        "active_control_agent": "C1_Drift_Agent",
    }


def run_full_onboarding_workflow(
    dataset: str,
    source_system: str,
    sample_dir: Path,
    registry_root: Path,
    adls_landing_path: str,
    auto_approve_gates: bool = True,
) -> dict[str, Any]:
    """Execute the 10-stage dataset onboarding workflow end-to-end."""
    # Stage 1: A0 Intake Agent
    manifest = run_a0_intake(
        dataset=dataset,
        source_system=source_system,
        sample_dir=sample_dir,
        registry_root=registry_root,
        adls_landing_path=adls_landing_path,
    )

    # Stage 2: C0 Schema Bootstrap Agent
    mapping = run_c0_bootstrap(manifest=manifest, registry_root=registry_root)

    if not auto_approve_gates:
        return {
            "stage": "PAUSED_AT_STAGE_3_C3_SCHEMA_REVIEW",
            "dataset": dataset,
            "fields_inferred": len(mapping.fields),
            "bootstrap_report": str(registry_root / dataset / "bootstrap_report.md"),
        }

    # Stage 3: C3 Schema Review Gate (Steward approves v1.0.0-bootstrap)
    approve_c3_schema_review(dataset=dataset, registry_root=registry_root)

    # Stage 4: A1 DDL Deployment Agent
    provision_info = run_a1_provision(dataset=dataset, registry_root=registry_root)

    # Stage 5: A2 Catalog Agent
    catalog_info = run_a2_catalog(dataset=dataset, registry_root=registry_root)

    # Stage 6: A3 Quality Gate Agent
    gates_info = deploy_a3_quality_gates(dataset=dataset, registry_root=registry_root)

    # Stage 7: A4 Monitoring Agent
    monitoring_info = run_a4_monitoring(dataset=dataset, registry_root=registry_root)

    # Stage 8: A5 Smoke Test Agent
    smoke_metrics = run_a5_smoke_test(dataset=dataset, registry_root=registry_root)
    if not smoke_metrics["smoke_test_passed"]:
        raise RuntimeError(f"Stage 8 Smoke Test failed for {dataset}: {smoke_metrics}")

    # Stage 9 & 10: C3 Go-Live Gate -> Dataset Live
    go_live_info = approve_c3_go_live(dataset=dataset, registry_root=registry_root)

    return {
        "dataset": dataset,
        "status": go_live_info["status"],
        "version": mapping.version,
        "fields_inferred": len(mapping.fields),
        "business_keys": mapping.business_keys,
        "provisioned_objects": provision_info["provisioned_objects"],
        "datahub_entities": catalog_info["entities"],
        "deployed_gates": list(gates_info["gates"].keys()),
        "sla_dashboard_view": monitoring_info["o5_sla_dashboard_view"],
        "smoke_test": smoke_metrics,
        "go_live": go_live_info,
    }


def process_runtime_file_with_drift_control(
    dataset: str,
    xml_file: Path,
    registry_root: Path,
) -> dict[str, Any]:
    """Run an incoming XML file through C1/C2 drift control and G1/G2/G3 quality gates."""
    ds_registry = registry_root / dataset
    findings = detect_schema_drift(xml_file=xml_file, registry_root=registry_root, dataset=dataset)
    proposal = None
    if findings:
        proposal = handle_drift_findings(dataset=dataset, registry_root=registry_root, findings=findings)

    # Now run the file through G1 -> G2 -> G3 -> D4 (or O3 Quarantine if breaking/invalid)
    ingest_metrics = ingest_xml_files_into_warehouse([xml_file], ds_registry)
    return {
        "file": xml_file.name,
        "drift_findings_count": len(findings),
        "proposal_status": proposal.status if proposal else "NO_DRIFT",
        "proposed_version": proposal.proposed_version if proposal else None,
        "ingest_metrics": ingest_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="XML to Snowflake Pipeline Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    ob = sub.add_parser("onboard", help="Run the 10-stage dataset onboarding workflow")
    ob.add_argument("--dataset", default="orders")
    ob.add_argument("--source-system", default="erp_orders")
    ob.add_argument("--sample-dir", default="samples/orders")
    ob.add_argument("--registry-root", default="registry")
    ob.add_argument("--adls-path", default="abfss://landing@enterpriseadls.dfs.core.windows.net/xml/orders/")

    dr = sub.add_parser("ingest", help="Ingest an XML file with C1/C2 drift detection and G1-G3 quality gates")
    dr.add_argument("--dataset", default="orders")
    dr.add_argument("--xml-file", required=True)
    dr.add_argument("--registry-root", default="registry")

    args = parser.parse_args()
    base = Path(__file__).resolve().parent.parent

    if args.command == "onboard":
        res = run_full_onboarding_workflow(
            dataset=args.dataset,
            source_system=args.source_system,
            sample_dir=base / args.sample_dir,
            registry_root=base / args.registry_root,
            adls_landing_path=args.adls_path,
            auto_approve_gates=True,
        )
        print(yaml.safe_dump(res, sort_keys=False))
    elif args.command == "ingest":
        res = process_runtime_file_with_drift_control(
            dataset=args.dataset,
            xml_file=base / args.xml_file,
            registry_root=base / args.registry_root,
        )
        print(yaml.safe_dump(res, sort_keys=False))


if __name__ == "__main__":
    main()
