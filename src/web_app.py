"""FastAPI / Starlette Web Backend for the XML-to-Snowflake Onboarding & Control Plane UI."""
from __future__ import annotations

from contextlib import closing
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
import yaml
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from src.agents.a0_intake import run_a0_intake
from src.agents.a1_provision import _sf_type_to_sqlite, run_a1_provision
from src.agents.a2_catalog import run_a2_catalog
from src.agents.a3_quality_gates import deploy_a3_quality_gates
from src.agents.a4_monitoring import run_a4_monitoring
from src.agents.a5_smoke_test import run_a5_smoke_test
from src.agents.c0_bootstrap import run_c0_bootstrap
from src.ddl_compiler import compile_snowflake_ddl
from src.models import (
    ContractSpec,
    DatasetMapping,
    OnboardingManifest,
    QualityRulesSpec,
)
from src.orchestrator import (
    approve_c3_go_live,
    approve_c3_schema_review,
    process_runtime_file_with_drift_control,
    run_full_onboarding_workflow,
)
from src.sample_generator import generate_samples
from src.xml_infer import build_snowflake_xml_expr

BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_ROOT = BASE_DIR / "registry"
SAMPLES_ROOT = BASE_DIR / "samples"
UI_HTML_PATH = Path(__file__).resolve().parent / "ui" / "index.html"


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _get_dataset_state(dataset: str) -> dict[str, Any]:
    ds_reg = REGISTRY_ROOT / dataset
    if not ds_reg.exists():
        return {"exists": False, "dataset": dataset}

    manifest = _load_yaml(ds_reg / "onboarding_manifest.yaml")
    mapping = _load_yaml(ds_reg / "mapping.yaml")
    contract = _load_yaml(ds_reg / "contract.yaml")
    quality_rules = _load_yaml(ds_reg / "quality_rules.yaml")
    datahub = _load_yaml(ds_reg / "datahub_urns.yaml")
    deployed_checks = _load_yaml(ds_reg / "deployed_checks.yaml")
    monitoring_cfg = _load_yaml(ds_reg / "monitoring_config.yaml")

    ddl_sql = (ds_reg / "ddl.sql").read_text(encoding="utf-8") if (ds_reg / "ddl.sql").exists() else ""
    monitoring_sql = (
        (ds_reg / "monitoring.sql").read_text(encoding="utf-8")
        if (ds_reg / "monitoring.sql").exists()
        else ""
    )
    bootstrap_report = (
        (ds_reg / "bootstrap_report.md").read_text(encoding="utf-8")
        if (ds_reg / "bootstrap_report.md").exists()
        else ""
    )
    smoke_report = (
        (ds_reg / "smoke_test_report.md").read_text(encoding="utf-8")
        if (ds_reg / "smoke_test_report.md").exists()
        else ""
    )

    # Read proposals
    proposals: list[dict[str, Any]] = []
    prop_dir = ds_reg / "proposals"
    if prop_dir.exists():
        for p in sorted(prop_dir.glob("*.md"), reverse=True):
            proposals.append(
                {
                    "name": p.name,
                    "version": p.stem.replace("proposal_", ""),
                    "markdown": p.read_text(encoding="utf-8"),
                }
            )

    # Read warehouse tables if provisioned
    curated_rows: list[dict[str, Any]] = []
    quarantine_rows: list[dict[str, Any]] = []
    dq_rows: list[dict[str, Any]] = []
    warehouse_counts = {
        "raw_rows": 0,
        "staging_rows": 0,
        "curated_current_rows": 0,
        "quarantine_open_rows": 0,
    }

    db_path = ds_reg / "local_warehouse.db"
    if db_path.exists() and mapping:
        targets = mapping.get("targets", {})
        with closing(sqlite3.connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute(f"SELECT COUNT(*) AS c FROM {targets['raw_table']}")
                warehouse_counts["raw_rows"] = cur.fetchone()["c"]

                cur.execute(f"SELECT COUNT(*) AS c FROM {targets['staging_table']}")
                warehouse_counts["staging_rows"] = cur.fetchone()["c"]

                cur.execute(f"SELECT COUNT(*) AS c FROM {targets['curated_table']} WHERE is_current = 1")
                warehouse_counts["curated_current_rows"] = cur.fetchone()["c"]

                cur.execute(f"SELECT COUNT(*) AS c FROM {targets['quarantine_table']} WHERE replayed = 0")
                warehouse_counts["quarantine_open_rows"] = cur.fetchone()["c"]

                cur.execute(f"SELECT * FROM {targets['curated_table']} ORDER BY system_start_time DESC LIMIT 50")
                curated_rows = [dict(r) for r in cur.fetchall()]

                cur.execute(f"SELECT * FROM {targets['quarantine_table']} ORDER BY quarantined_at DESC LIMIT 50")
                quarantine_rows = [dict(r) for r in cur.fetchall()]

                cur.execute(f"SELECT * FROM {targets['dq_results_table']} ORDER BY checked_at DESC LIMIT 60")
                dq_rows = [dict(r) for r in cur.fetchall()]
            except sqlite3.Error:
                pass

    # List available sample & drift test files
    available_test_files: list[str] = []
    for sub in ["orders", "orders_drift", dataset]:
        sdir = SAMPLES_ROOT / sub
        if sdir.exists():
            for xp in sorted(sdir.glob("*.xml")):
                rel = f"samples/{sub}/{xp.name}"
                if rel not in available_test_files:
                    available_test_files.append(rel)

    return {
        "exists": True,
        "dataset": dataset,
        "manifest": manifest,
        "mapping": mapping,
        "contract": contract,
        "quality_rules": quality_rules,
        "datahub": datahub,
        "deployed_checks": deployed_checks,
        "monitoring_config": monitoring_cfg,
        "ddl_sql": ddl_sql,
        "monitoring_sql": monitoring_sql,
        "bootstrap_report": bootstrap_report,
        "smoke_report": smoke_report,
        "proposals": proposals,
        "warehouse_counts": warehouse_counts,
        "curated_rows": curated_rows,
        "quarantine_rows": quarantine_rows,
        "dq_rows": dq_rows,
        "available_test_files": available_test_files,
    }


async def index_page(request: Request) -> HTMLResponse:
    return HTMLResponse(UI_HTML_PATH.read_text(encoding="utf-8"))


async def api_list_datasets(request: Request) -> JSONResponse:
    REGISTRY_ROOT.mkdir(parents=True, exist_ok=True)
    datasets = sorted(p.name for p in REGISTRY_ROOT.iterdir() if p.is_dir())
    if not datasets:
        generate_samples(BASE_DIR)
        run_full_onboarding_workflow(
            dataset="orders",
            source_system="erp_orders",
            sample_dir=SAMPLES_ROOT / "orders",
            registry_root=REGISTRY_ROOT,
            adls_landing_path="abfss://landing@enterpriseadls.dfs.core.windows.net/xml/orders/",
            auto_approve_gates=True,
        )
        datasets = ["orders"]
    active = request.query_params.get("dataset", datasets[0])
    return JSONResponse(
        {
            "datasets": datasets,
            "state": _get_dataset_state(active),
        }
    )


async def api_bootstrap(request: Request) -> JSONResponse:
    """Run Stage 1 (A0 Intake) + Stage 2 (C0 Bootstrap) and pause at Stage 3 (C3 Steward Review)."""
    body = await request.json()
    dataset = body.get("dataset", "orders").strip().lower()
    source_system = body.get("source_system", f"erp_{dataset}")
    adls_path = body.get(
        "adls_landing_path",
        f"abfss://landing@enterpriseadls.dfs.core.windows.net/xml/{dataset}/",
    )
    sample_dir_rel = body.get("sample_dir", "samples/orders")
    data_steward = body.get("data_steward", "data-steward@enterprise.io")
    engineering_owner = body.get("engineering_owner", "data-eng@enterprise.io")
    sla_hours = int(body.get("freshness_sla_hours", 24))
    conf_threshold = float(body.get("confidence_threshold", 0.8))

    sample_dir = BASE_DIR / sample_dir_rel
    if not sample_dir.exists():
        generate_samples(BASE_DIR)
        sample_dir = SAMPLES_ROOT / "orders"

    # Optional custom XML file uploaded from the UI
    custom_xml_name = body.get("custom_xml_name", "").strip()
    custom_xml_content = body.get("custom_xml_content", "").strip()
    if custom_xml_name and custom_xml_content:
        if not custom_xml_name.endswith(".xml"):
            custom_xml_name += ".xml"
        (sample_dir / custom_xml_name).write_text(custom_xml_content, encoding="utf-8")

    manifest = run_a0_intake(
        dataset=dataset,
        source_system=source_system,
        sample_dir=sample_dir,
        registry_root=REGISTRY_ROOT,
        adls_landing_path=adls_path,
        data_steward=data_steward,
        engineering_owner=engineering_owner,
        freshness_sla_hours=sla_hours,
    )
    run_c0_bootstrap(
        manifest=manifest,
        registry_root=REGISTRY_ROOT,
        confidence_threshold=conf_threshold,
    )
    return JSONResponse({"ok": True, "state": _get_dataset_state(dataset)})


async def api_save_schema_overrides(request: Request) -> JSONResponse:
    """Save Data Steward C3 edits to mapping.yaml, contract.yaml, quality_rules.yaml, and recompile ddl.sql."""
    body = await request.json()
    dataset = body["dataset"]
    ds_reg = REGISTRY_ROOT / dataset

    mapping = DatasetMapping.model_validate(_load_yaml(ds_reg / "mapping.yaml"))
    contract = ContractSpec.model_validate(_load_yaml(ds_reg / "contract.yaml"))
    rules = QualityRulesSpec.model_validate(_load_yaml(ds_reg / "quality_rules.yaml"))

    updated_fields_data = body.get("fields", [])
    business_keys = body.get("business_keys", mapping.business_keys)
    root_tag = mapping.root_element.strip("/")

    by_xpath = {f.xpath: f for f in mapping.fields}
    for uf in updated_fields_data:
        xp = uf["xpath"]
        if xp in by_xpath:
            f = by_xpath[xp]
            f.column = uf["column"].strip()
            f.snowflake_type = uf["snowflake_type"].strip()
            f.required = bool(uf["required"])
            f.origin = "c3_steward_override"
            f.xml_expr = build_snowflake_xml_expr(
                xpath=f.xpath,
                root_tag=root_tag,
                sf_type=f.snowflake_type,
                is_array=f.is_array,
                flatten_path=f.flatten_path,
                is_attribute=f.is_attribute,
            )

    mapping.business_keys = business_keys
    (ds_reg / "mapping.yaml").write_text(
        yaml.safe_dump(mapping.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # Sync contract.yaml
    contract.required_xpaths = [f.xpath for f in mapping.fields if f.required]
    contract.type_assertions = {f.xpath: f.snowflake_type for f in mapping.fields}
    (ds_reg / "contract.yaml").write_text(
        yaml.safe_dump(contract.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # Sync quality_rules.yaml
    rules.primary_keys = business_keys
    rules.not_null_columns = [f.column for f in mapping.fields if f.required]
    if "accepted_values" in body:
        rules.accepted_values = body["accepted_values"]
    (ds_reg / "quality_rules.yaml").write_text(
        yaml.safe_dump(rules.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # Recompile ddl.sql
    (ds_reg / "ddl.sql").write_text(compile_snowflake_ddl(mapping), encoding="utf-8")

    return JSONResponse({"ok": True, "state": _get_dataset_state(dataset)})


async def api_approve_schema_and_provision(request: Request) -> JSONResponse:
    """Execute Stage 3 (C3 Schema Approve) -> Stage 4 (A1) -> Stage 5 (A2) -> Stage 6 (A3) -> Stage 7 (A4) -> Stage 8 (A5 Smoke Test)."""
    body = await request.json()
    dataset = body["dataset"]

    approve_c3_schema_review(dataset, REGISTRY_ROOT)
    run_a1_provision(dataset, REGISTRY_ROOT)
    run_a2_catalog(dataset, REGISTRY_ROOT)
    deploy_a3_quality_gates(dataset, REGISTRY_ROOT)
    run_a4_monitoring(dataset, REGISTRY_ROOT)
    smoke = run_a5_smoke_test(dataset, REGISTRY_ROOT)

    return JSONResponse({"ok": True, "smoke_test": smoke, "state": _get_dataset_state(dataset)})


async def api_approve_go_live(request: Request) -> JSONResponse:
    """Execute Stage 9 & 10 (C3 Go-Live Gate -> Enable Snowpipe & mark PUBLISHED)."""
    body = await request.json()
    dataset = body["dataset"]
    go_live = approve_c3_go_live(dataset, REGISTRY_ROOT)
    return JSONResponse({"ok": True, "go_live": go_live, "state": _get_dataset_state(dataset)})


async def api_ingest_xml(request: Request) -> JSONResponse:
    """Ingest a file (or custom XML) through C1/C2 Drift Detection and G1/G2/G3 Quality Gates."""
    body = await request.json()
    dataset = body["dataset"]
    xml_rel_path = body.get("xml_file", "").strip()
    custom_xml = body.get("custom_xml", "").strip()
    custom_name = body.get("custom_name", "custom_upload.xml").strip()

    if custom_xml:
        drift_dir = SAMPLES_ROOT / "orders_drift"
        drift_dir.mkdir(parents=True, exist_ok=True)
        if not custom_name.endswith(".xml"):
            custom_name += ".xml"
        xml_path = drift_dir / custom_name
        xml_path.write_text(custom_xml, encoding="utf-8")
    else:
        xml_path = BASE_DIR / xml_rel_path

    res = process_runtime_file_with_drift_control(
        dataset=dataset,
        xml_file=xml_path,
        registry_root=REGISTRY_ROOT,
    )
    return JSONResponse({"ok": True, "result": res, "state": _get_dataset_state(dataset)})


async def api_replay_quarantine(request: Request) -> JSONResponse:
    """Mark quarantined records in O3 as resolved/replayed after steward or engineering fix."""
    body = await request.json()
    dataset = body["dataset"]
    ds_reg = REGISTRY_ROOT / dataset
    mapping = _load_yaml(ds_reg / "mapping.yaml")
    db_path = ds_reg / "local_warehouse.db"
    if db_path.exists() and mapping:
        q_table = mapping["targets"]["quarantine_table"]
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(f"UPDATE {q_table} SET replayed = 1 WHERE replayed = 0")
            conn.commit()
    return JSONResponse({"ok": True, "state": _get_dataset_state(dataset)})


routes = [
    Route("/", index_page, methods=["GET"]),
    Route("/api/state", api_list_datasets, methods=["GET"]),
    Route("/api/bootstrap", api_bootstrap, methods=["POST"]),
    Route("/api/save-schema", api_save_schema_overrides, methods=["POST"]),
    Route("/api/provision", api_approve_schema_and_provision, methods=["POST"]),
    Route("/api/go-live", api_approve_go_live, methods=["POST"]),
    Route("/api/ingest", api_ingest_xml, methods=["POST"]),
    Route("/api/replay-quarantine", api_replay_quarantine, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
