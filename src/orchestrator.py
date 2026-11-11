"""End-to-End Orchestrator for XML Dataset Onboarding and Runtime Drift Control.

Workflow:
- Step 1: Data Steward Agent (Intake + XML schema inference, 3-layer YAML schemas & data modeling — NO DDL)
- C3 Gate: Human Approval on Data Model & 3-Layer YAML Schemas (`raw_schema.yaml`, `staging_schema.yaml`, `gold_schema.yaml`)
- Step 2: DDL Generator Agent (Compiles Snowpipe + Stage Dynamic Table + Gold Dynamic Table SQLs & deployment manifest)
- Step 3: Pipeline Deployment Agent (Deploys SQLs & creates E2E pipelines from ADLS to Final Gold layer, except DataHub)
- Stages 5–10: Catalog Agent (A2), Quality Gate Agent (A3), Monitoring Agent (A4), Smoke Test Agent (A5), Go-Live Gate (C3)
"""
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
from src.agents.c0_bootstrap import run_data_steward_agent
from src.agents.c1_drift_agent import detect_schema_drift
from src.agents.c2_proposal_agent import handle_drift_findings
from src.agents.ddl_generator_agent import run_ddl_generator_agent
from src.archival_manager import archive_ingested_file
from src.dq_report_generator import generate_compliance_certificate
from src.hierarchical_dq import audit_xml_hierarchical_integrity
from src.models import DataModelSpec, OnboardingManifest
from src.reconciliation_auditor import run_reconciliation_audit
from src.snowflake_client import (
    deploy_pipeline_to_snowflake_external_browser,
    load_snowflake_config,
)


def approve_c3_schema_review(dataset: str, registry_root: Path) -> None:
    """C3 Human Approval Gate: Approves data_model.yaml and 3-layer YAML schemas (Raw, Stage, Gold)."""
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

    dm_path = ds_registry / "data_model.yaml"
    if dm_path.exists():
        dm = DataModelSpec.model_validate(
            yaml.safe_load(dm_path.read_text(encoding="utf-8"))
        )
        dm.approval_status = "APPROVED"
        dm_path.write_text(
            yaml.safe_dump(dm.model_dump(), sort_keys=False),
            encoding="utf-8",
        )


def approve_c3_go_live(
    dataset: str,
    registry_root: Path,
    deploy_to_snowflake: bool = False,
) -> dict[str, Any]:
    """Stage 9 & 10 — C3 Go-Live Gate: Engineering approves smoke test, connects to Snowflake via External Browser SSO, and deploys the pipeline."""
    ds_registry = registry_root / dataset
    manifest_path = ds_registry / "onboarding_manifest.yaml"

    sf_deployment: dict[str, Any] | None = None
    sf_cfg = load_snowflake_config()
    if deploy_to_snowflake or (sf_cfg.mode == "externalbrowser" and sf_cfg.is_configured):
        sf_deployment = deploy_pipeline_to_snowflake_external_browser(
            dataset=dataset,
            registry_root=registry_root,
            cfg=sf_cfg,
            enable_snowpipe=True,
            seed_sample_xmls=True,
        )

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
        "snowflake_live_deployment": sf_deployment,
    }


def run_full_onboarding_workflow(
    dataset: str,
    source_system: str,
    sample_dir: Path,
    registry_root: Path,
    adls_landing_path: str,
    auto_approve_gates: bool = True,
) -> dict[str, Any]:
    """Execute the dataset onboarding workflow end-to-end."""
    # Step 1: Intake + Data Steward Agent (generates 3-layer YAML schemas & data model — NO DDL)
    manifest = run_a0_intake(
        dataset=dataset,
        source_system=source_system,
        sample_dir=sample_dir,
        registry_root=registry_root,
        adls_landing_path=adls_landing_path,
    )
    mapping = run_data_steward_agent(manifest=manifest, registry_root=registry_root)

    if not auto_approve_gates:
        return {
            "stage": "PAUSED_AT_STAGE_3_C3_SCHEMA_REVIEW",
            "dataset": dataset,
            "fields_inferred": len(mapping.fields),
            "raw_schema_yaml": str(registry_root / dataset / "raw_schema.yaml"),
            "staging_schema_yaml": str(registry_root / dataset / "staging_schema.yaml"),
            "gold_schema_yaml": str(registry_root / dataset / "gold_schema.yaml"),
            "data_model_yaml": str(registry_root / dataset / "data_model.yaml"),
            "bootstrap_report": str(registry_root / dataset / "bootstrap_report.md"),
        }

    # Human Gate (C3): Approve data model & 3-layer YAML schemas
    approve_c3_schema_review(dataset=dataset, registry_root=registry_root)

    # Step 2: DDL Generator Agent (generates SQLs for all 3 layers + deployment artifacts)
    ddl_manifest = run_ddl_generator_agent(dataset=dataset, registry_root=registry_root)

    # Step 3: Pipeline Deployment Agent (deploys SQLs & creates E2E pipelines from ADLS to Final Gold)
    provision_info = run_a1_provision(dataset=dataset, registry_root=registry_root)

    # Stage 5: A2 Catalog Agent (stays as is)
    catalog_info = run_a2_catalog(dataset=dataset, registry_root=registry_root)

    # Stage 6: A3 Quality Gate Agent (stays as is)
    gates_info = deploy_a3_quality_gates(dataset=dataset, registry_root=registry_root)

    # Stage 7: A4 Monitoring Agent (stays as is)
    monitoring_info = run_a4_monitoring(dataset=dataset, registry_root=registry_root)

    # Stage 8: A5 Smoke Test Agent (stays as is)
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
        "layer_schemas": {
            "raw": str(registry_root / dataset / "raw_schema.yaml"),
            "stage": str(registry_root / dataset / "staging_schema.yaml"),
            "gold": str(registry_root / dataset / "gold_schema.yaml"),
            "data_model": str(registry_root / dataset / "data_model.yaml"),
        },
        "ddl_artifacts": ddl_manifest.sql_artifacts,
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

    # Automatically compute zero-loss reconciliation and generate compliance certificate
    recon_audit = run_reconciliation_audit(dataset, xml_file, registry_root)
    cert_meta = generate_compliance_certificate(dataset, xml_file, registry_root)

    # Automatically archive file with GZIP compression if ingestion passed
    archive_meta = None
    if ingest_metrics.get("files_passed", 0) > 0:
        try:
            archive_root = registry_root.parent / "archive"
            archive_meta = archive_ingested_file(xml_file, archive_root, dataset)
        except Exception:
            pass

    return {
        "file": xml_file.name,
        "drift_findings_count": len(findings),
        "proposal_status": proposal.status if proposal else "NO_DRIFT",
        "proposed_version": proposal.proposed_version if proposal else None,
        "ingest_metrics": ingest_metrics,
        "reconciliation": recon_audit,
        "compliance_certificate": cert_meta,
        "archive": archive_meta,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="XML to Snowflake Pipeline Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    ob = sub.add_parser("onboard", help="Run the dataset onboarding workflow")
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
