"""FastAPI / Starlette Web Backend for the XML-to-Snowflake Onboarding & Control Plane UI."""
from __future__ import annotations

from contextlib import closing
import json
import os
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
from src.agents.a1_provision import run_a1_provision
from src.agents.a2_catalog import run_a2_catalog
from src.agents.a3_quality_gates import deploy_a3_quality_gates
from src.agents.a4_monitoring import run_a4_monitoring
from src.agents.a5_smoke_test import run_a5_smoke_test
from src.agents.c0_bootstrap import _build_three_layer_data_model, run_c0_bootstrap
from src.agents.ddl_generator_agent import run_ddl_generator_agent
from src.alert_dispatcher import AlertNotification, dispatch_alert
from src.dbt_exporter import export_dbt_project
from src.dq_report_generator import generate_compliance_certificate
from src.entity_model import build_entity_model, render_er_diagram
from src.hierarchical_dq import audit_xml_hierarchical_integrity
from src.llm.anthropic_client import load_llm_config
from src.models import (
    ContractSpec,
    DatasetMapping,
    FieldMapping,
    QualityRulesSpec,
)
from src.orchestrator import (
    approve_c3_go_live,
    approve_c3_schema_review,
    process_runtime_file_with_drift_control,
    run_full_onboarding_workflow,
)
from src.sample_generator import generate_samples
from src.schema_diff import compare_mappings, generate_changelog_markdown
from src.schema_exporter import export_json_schema, export_openapi_spec
from src.snowflake_client import (
    deploy_pipeline_to_snowflake_external_browser,
    get_snowflake_status,
    load_snowflake_config,
    test_snowflake_external_browser_connection,
    update_snowflake_config,
)
from src.xml_infer import build_snowflake_xml_expr

BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRY_ROOT = BASE_DIR / "registry"
SAMPLES_ROOT = BASE_DIR / "samples"
DATASETS_ROOT = BASE_DIR / "datasets"
UI_HTML_PATH = Path(__file__).resolve().parent / "ui" / "index.html"


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _get_llm_status() -> dict[str, Any]:
    cfg = load_llm_config()
    key = cfg.api_key or ""
    masked = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else ("***set***" if key else "")
    return {
        "enabled": cfg.enabled,
        "provider": cfg.provider,
        "model": cfg.model,
        "api_key_env": cfg.api_key_env,
        "api_key_set": bool(key),
        "api_key_masked": masked,
        "is_available": cfg.is_available,
    }


def _get_dataset_state(dataset: str) -> dict[str, Any]:
    ds_reg = REGISTRY_ROOT / dataset
    if not ds_reg.exists():
        return {
            "exists": False,
            "dataset": dataset,
            "llm_status": _get_llm_status(),
            "snowflake_status": get_snowflake_status(),
        }

    manifest = _load_yaml(ds_reg / "onboarding_manifest.yaml")
    mapping = _load_yaml(ds_reg / "mapping.yaml")
    raw_schema = _load_yaml(ds_reg / "raw_schema.yaml")
    staging_schema = _load_yaml(ds_reg / "staging_schema.yaml")
    gold_schema = _load_yaml(ds_reg / "gold_schema.yaml")
    data_model = _load_yaml(ds_reg / "data_model.yaml")
    if data_model and mapping and not data_model.get("er_diagram_staging"):
        # Older registry entries: derive the parent/child ER diagrams on the fly from the field inventory
        try:
            em = build_entity_model(DatasetMapping.model_validate(mapping))
            data_model["er_diagram_staging"] = render_er_diagram(em, "STAGE")
            data_model["er_diagram_curated"] = render_er_diagram(em, "GOLD")
        except Exception:  # noqa: BLE001 - diagram is advisory only
            pass
    deployment_manifest = _load_yaml(ds_reg / "pipeline_deployment_manifest.yaml")
    provisioned_objects = _load_yaml(ds_reg / "provisioned_objects.yaml")
    snowflake_live_deployment = _load_yaml(ds_reg / "snowflake_live_deployment.yaml")
    signoff_record = _load_yaml(ds_reg / "signoff_record.yaml")
    contract = _load_yaml(ds_reg / "contract.yaml")
    quality_rules = _load_yaml(ds_reg / "quality_rules.yaml")
    datahub = _load_yaml(ds_reg / "datahub_urns.yaml")
    deployed_checks = _load_yaml(ds_reg / "deployed_checks.yaml")
    monitoring_cfg = _load_yaml(ds_reg / "monitoring_config.yaml")

    yaml_files_text = {
        "raw_schema.yaml": _read_text(ds_reg / "raw_schema.yaml"),
        "staging_schema.yaml": _read_text(ds_reg / "staging_schema.yaml"),
        "gold_schema.yaml": _read_text(ds_reg / "gold_schema.yaml"),
        "data_model.yaml": _read_text(ds_reg / "data_model.yaml"),
        "mapping.yaml": _read_text(ds_reg / "mapping.yaml"),
        "contract.yaml": _read_text(ds_reg / "contract.yaml"),
        "quality_rules.yaml": _read_text(ds_reg / "quality_rules.yaml"),
    }

    sql_dir = ds_reg / "sql"
    sql_files_text = {
        "01_raw_snowpipe.sql": _read_text(sql_dir / "01_raw_snowpipe.sql"),
        "02_staging_dynamic_table.sql": _read_text(sql_dir / "02_staging_dynamic_table.sql"),
        "03_gold_dynamic_table.sql": _read_text(sql_dir / "03_gold_dynamic_table.sql"),
        "04_ops_quarantine_dq.sql": _read_text(sql_dir / "04_ops_quarantine_dq.sql"),
        "ddl.sql": _read_text(ds_reg / "ddl.sql"),
        "pipeline_deployment_manifest.yaml": _read_text(ds_reg / "pipeline_deployment_manifest.yaml"),
    }

    ddl_sql = _read_text(ds_reg / "ddl.sql")
    monitoring_sql = _read_text(ds_reg / "monitoring.sql")
    bootstrap_report = _read_text(ds_reg / "bootstrap_report.md")
    smoke_report = _read_text(ds_reg / "smoke_test_report.md")

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
    for sub in ["orders", "orders_drift", "analytics_drift", dataset, f"{dataset}_drift"]:
        sdir = SAMPLES_ROOT / sub
        if sdir.exists():
            for xp in sorted(sdir.glob("*.xml")):
                rel = f"samples/{sub}/{xp.name}"
                if rel not in available_test_files:
                    available_test_files.append(rel)
    ent_samples = DATASETS_ROOT / "enterprise_orders" / "samples"
    if ent_samples.exists():
        for xp in sorted(ent_samples.glob("*.xml")):
            rel = f"datasets/enterprise_orders/samples/{xp.name}"
            if rel not in available_test_files:
                available_test_files.append(rel)

    return {
        "exists": True,
        "dataset": dataset,
        "llm_status": _get_llm_status(),
        "snowflake_status": get_snowflake_status(),
        "manifest": manifest,
        "mapping": mapping,
        "raw_schema": raw_schema,
        "staging_schema": staging_schema,
        "gold_schema": gold_schema,
        "data_model": data_model,
        "deployment_manifest": deployment_manifest,
        "provisioned_objects": provisioned_objects,
        "snowflake_live_deployment": snowflake_live_deployment,
        "signoff_record": signoff_record,
        "yaml_files_text": yaml_files_text,
        "sql_files_text": sql_files_text,
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
        "hierarchical_audit": _audit_sample_file(dataset, manifest),
    }


def _audit_sample_file(dataset: str, manifest: dict[str, Any] | None) -> dict[str, Any] | None:
    if not manifest:
        return None
    sample_dir = Path(manifest.get("onboarding_sample_dir", ""))
    sample_files = manifest.get("valid_sample_files", [])
    if sample_files and sample_dir.exists():
        target_file = sample_dir / sample_files[0]
        if target_file.exists():
            try:
                return audit_xml_hierarchical_integrity(target_file)
            except Exception:
                return None
    return None


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
            "llm_status": _get_llm_status(),
            "snowflake_status": get_snowflake_status(),
            "state": _get_dataset_state(active),
        }
    )


async def api_configure_llm(request: Request) -> JSONResponse:
    """Save Anthropic API key & default model (claude-haiku-5-5) from the UI and optionally ping Anthropic."""
    body = await request.json()
    api_key = body.get("api_key", "").strip()
    model = body.get("model", "claude-haiku-5-5").strip() or "claude-haiku-5-5"
    enabled = bool(body.get("enabled", True))
    test_conn = bool(body.get("test_connection", False))

    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif body.get("clear_key"):
        os.environ.pop("ANTHROPIC_API_KEY", None)

    os.environ["XML_PIPELINE_LLM_MODEL"] = model
    os.environ["XML_PIPELINE_LLM_ENABLED"] = "true" if enabled else "false"

    ping_result = None
    if test_conn:
        cfg = load_llm_config()
        if not cfg.api_key:
            return JSONResponse(
                {"ok": False, "error": "No Anthropic API key provided.", "llm_status": _get_llm_status()},
                status_code=400,
            )
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=cfg.api_key, timeout=20.0)
            resp = client.messages.create(
                model=cfg.model,
                max_tokens=16,
                messages=[{"role": "user", "content": "Reply with OK."}],
            )
            ping_result = "".join(getattr(b, "text", "") for b in resp.content).strip()
        except Exception as exc:
            return JSONResponse(
                {"ok": False, "error": f"Anthropic connection failed: {exc}", "llm_status": _get_llm_status()},
                status_code=400,
            )

    return JSONResponse({"ok": True, "ping_result": ping_result, "llm_status": _get_llm_status()})


async def api_bootstrap(request: Request) -> JSONResponse:
    """Step 1: Save uploaded local XML file(s), apply optional Anthropic API key, and run Data Steward Agent (generates YAMLs, NO DDL)."""
    body = await request.json()
    dataset = body.get("dataset", "orders").strip().lower().replace(" ", "_")
    source_system = body.get("source_system", f"erp_{dataset}")
    adls_path = body.get(
        "adls_landing_path",
        f"abfss://landing@enterpriseadls.dfs.core.windows.net/xml/{dataset}/",
    )
    sample_dir_rel = body.get("sample_dir", f"samples/{dataset}").strip()
    data_steward = body.get("data_steward", "data-steward@enterprise.io")
    engineering_owner = body.get("engineering_owner", "data-eng@enterprise.io")
    sla_hours = int(body.get("freshness_sla_hours", 24))
    conf_threshold = float(body.get("confidence_threshold", 0.8))

    # Apply Anthropic API Key & Model if provided inline in the form
    inline_key = body.get("anthropic_api_key", "").strip()
    inline_model = body.get("llm_model", "").strip()
    if inline_key:
        os.environ["ANTHROPIC_API_KEY"] = inline_key
        os.environ["XML_PIPELINE_LLM_ENABLED"] = "true"
    if inline_model:
        os.environ["XML_PIPELINE_LLM_MODEL"] = inline_model

    # Handle local files selected via browser file input
    uploaded_files: list[dict[str, str]] = body.get("uploaded_files") or []
    custom_xml_name = body.get("custom_xml_name", "").strip()
    custom_xml_content = body.get("custom_xml_content", "").strip()
    if custom_xml_name and custom_xml_content:
        uploaded_files.append({"name": custom_xml_name, "content": custom_xml_content})

    if uploaded_files:
        sample_dir = SAMPLES_ROOT / dataset
        if body.get("replace_existing_samples", True) and sample_dir.exists():
            for old_xml in sample_dir.glob("*.xml"):
                old_xml.unlink()
        sample_dir.mkdir(parents=True, exist_ok=True)
        for uf in uploaded_files:
            fname = Path(uf.get("name", "sample.xml")).name
            if not fname.endswith(".xml"):
                fname += ".xml"
            (sample_dir / fname).write_text(uf.get("content", ""), encoding="utf-8")
    else:
        sample_dir = BASE_DIR / sample_dir_rel
        if not sample_dir.exists():
            generate_samples(BASE_DIR)
            sample_dir = SAMPLES_ROOT / "orders"

    try:
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
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)

    datasets = sorted(p.name for p in REGISTRY_ROOT.iterdir() if p.is_dir())
    return JSONResponse({"ok": True, "datasets": datasets, "state": _get_dataset_state(dataset)})


async def api_save_schema_overrides(request: Request) -> JSONResponse:
    """Save Data Steward C3 edits to mapping.yaml, contract.yaml, quality_rules.yaml, and 3-layer YAML schemas (NO DDL yet)."""
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

    # Sync 3-layer YAML schemas & data_model.yaml (preserve any existing LLM proposal)
    existing_dm = _load_yaml(ds_reg / "data_model.yaml") or {}
    raw_schema, staging_schema, gold_schema, data_model = _build_three_layer_data_model(mapping)
    if existing_dm.get("llm_proposal"):
        data_model.modeling_engine = existing_dm.get("modeling_engine", "anthropic_claude")
        data_model.llm_model = existing_dm.get("llm_model")
        data_model.llm_proposal = existing_dm.get("llm_proposal")

    (ds_reg / "raw_schema.yaml").write_text(
        yaml.safe_dump(raw_schema.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    (ds_reg / "staging_schema.yaml").write_text(
        yaml.safe_dump(staging_schema.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    (ds_reg / "gold_schema.yaml").write_text(
        yaml.safe_dump(gold_schema.model_dump(), sort_keys=False),
        encoding="utf-8",
    )
    (ds_reg / "data_model.yaml").write_text(
        yaml.safe_dump(data_model.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    return JSONResponse({"ok": True, "state": _get_dataset_state(dataset)})


async def api_approve_yamls_and_generate_ddl(request: Request) -> JSONResponse:
    """Human approves 3-layer YAMLs & Data Model -> Triggers Step 2: DDL Generator Agent to generate all SQLs."""
    body = await request.json()
    dataset = body["dataset"]

    approve_c3_schema_review(dataset, REGISTRY_ROOT)
    ddl_manifest = run_ddl_generator_agent(dataset, REGISTRY_ROOT)
    return JSONResponse(
        {
            "ok": True,
            "ddl_manifest": ddl_manifest.model_dump(),
            "state": _get_dataset_state(dataset),
        }
    )


async def api_approve_schema_and_provision(request: Request) -> JSONResponse:
    """Execute C3 Human Approval -> Step 2 (DDL Generator Agent) -> Step 3 (Pipeline Deployment Agent) -> A2 -> A3 -> A4 -> A5."""
    body = await request.json()
    dataset = body["dataset"]

    approve_c3_schema_review(dataset, REGISTRY_ROOT)
    run_ddl_generator_agent(dataset, REGISTRY_ROOT)
    run_a1_provision(dataset, REGISTRY_ROOT)
    run_a2_catalog(dataset, REGISTRY_ROOT)
    deploy_a3_quality_gates(dataset, REGISTRY_ROOT)
    run_a4_monitoring(dataset, REGISTRY_ROOT)
    smoke = run_a5_smoke_test(dataset, REGISTRY_ROOT)

    return JSONResponse({"ok": True, "smoke_test": smoke, "state": _get_dataset_state(dataset)})


async def api_configure_snowflake(request: Request) -> JSONResponse:
    """Save Snowflake External Browser SSO configuration from the UI and optionally trigger browser SSO login test."""
    body = await request.json()
    update_snowflake_config(body)
    test_conn = bool(body.get("test_connection", False))

    session_info = None
    if test_conn:
        try:
            session_info = test_snowflake_external_browser_connection()
        except Exception as exc:
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"Snowflake External Browser SSO failed: {exc}",
                    "snowflake_status": get_snowflake_status(),
                },
                status_code=400,
            )

    return JSONResponse(
        {
            "ok": True,
            "session": session_info,
            "snowflake_status": get_snowflake_status(),
        }
    )


async def api_approve_go_live(request: Request) -> JSONResponse:
    """Execute Stage 9 & 10 (Final Engineering Sign-Off -> Connect to Snowflake via External Browser SSO, deploy pipeline & mark PUBLISHED)."""
    body = await request.json()
    dataset = body["dataset"]
    signed_off_by = body.get("signed_off_by", "data-eng@enterprise.io").strip()
    signoff_notes = body.get("signoff_notes", "Approved all 3-layer DDLs, Dynamic Tables, and Smoke Test.").strip()
    deploy_live = bool(body.get("deploy_to_snowflake", False))

    # Apply any inline Snowflake connection details sent from the Final Sign-Off card
    sf_inline = body.get("snowflake_config")
    if isinstance(sf_inline, dict) and sf_inline:
        update_snowflake_config(sf_inline)

    sf_cfg = load_snowflake_config()
    if deploy_live and not sf_cfg.is_configured:
        return JSONResponse(
            {
                "ok": False,
                "error": "Snowflake Account Identifier is required to connect via External Browser SSO (e.g. 'xy12345.us-east-1' or 'orgname-accountname'). Please fill in the Snowflake Account field.",
                "snowflake_status": get_snowflake_status(),
            },
            status_code=400,
        )

    try:
        # Re-compile Step 2 SQL scripts & monitoring SQL with the active Snowflake layer schema names
        run_ddl_generator_agent(dataset, REGISTRY_ROOT)
        run_a4_monitoring(dataset, REGISTRY_ROOT)
        go_live = approve_c3_go_live(
            dataset=dataset,
            registry_root=REGISTRY_ROOT,
            deploy_to_snowflake=deploy_live,
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "error": f"Snowflake External Browser deployment failed: {exc}",
                "snowflake_status": get_snowflake_status(),
                "state": _get_dataset_state(dataset),
            },
            status_code=400,
        )

    go_live["signed_off_by"] = signed_off_by
    go_live["signoff_notes"] = signoff_notes
    go_live["signed_off_at"] = datetime.now(timezone.utc).isoformat()

    ds_reg = REGISTRY_ROOT / dataset
    (ds_reg / "signoff_record.yaml").write_text(
        yaml.safe_dump(go_live, sort_keys=False),
        encoding="utf-8",
    )
    return JSONResponse(
        {
            "ok": True,
            "go_live": go_live,
            "snowflake_status": get_snowflake_status(),
            "state": _get_dataset_state(dataset),
        }
    )


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


async def api_approve_child_entity(request: Request) -> JSONResponse:
    """Approve and integrate a newly detected repeating child entity into the dataset mapping, data model, and DDLs."""
    body = await request.json()
    dataset = body["dataset"]
    proposal = body["proposal"]
    ds_reg = REGISTRY_ROOT / dataset
    mapping_path = ds_reg / "mapping.yaml"

    if not mapping_path.exists():
        return JSONResponse({"ok": False, "error": f"Dataset {dataset} not found"}, status_code=404)

    mapping_data = _load_yaml(mapping_path)
    mapping = DatasetMapping.model_validate(mapping_data)

    container_tag = proposal["container_tag"]
    record_tag = proposal["record_tag"]
    entity_name = proposal["entity_name"].replace(f"{dataset}_", "")

    # Base path for child record elements
    root_tag = mapping.root_element.strip("/").split("/")[0]
    base_xpath = f"/{root_tag}/ASSET/BND_CORP/{container_tag}/{record_tag}"

    # Append new fields
    existing_xpaths = {f.xpath for f in mapping.fields}
    added_fields = []
    for col in proposal.get("columns", []):
        leaf_tag = col.get("tag", col["name"].upper())
        leaf_xpath = f"{base_xpath}/{leaf_tag}"
        if leaf_xpath not in existing_xpaths:
            col_type = col.get("type", "VARCHAR")
            new_f = FieldMapping(
                xpath=leaf_xpath,
                column=f"{entity_name}_{col['name']}",
                snowflake_type=col_type,
                xml_expr=f"XMLGET(item.value, '{leaf_tag}'):\"$\"::{col_type}",
                required=False,
                is_array=True,
                flatten_path=base_xpath,
                is_attribute=False,
                confidence=1.0,
                sample_values=[],
                origin="c3_steward_override",
                added_in_version=mapping.version,
            )
            mapping.fields.append(new_f)
            added_fields.append(col["name"])

    # Bump version
    parts = mapping.version.split(".")
    if len(parts) == 3 and parts[1].isdigit():
        mapping.version = f"{parts[0]}.{int(parts[1]) + 1}.0"

    # Save updated mapping.yaml
    mapping_path.write_text(yaml.safe_dump(mapping.model_dump(), sort_keys=False), encoding="utf-8")

    # Reconstruct 3-layer schemas and data model
    raw_s, stage_s, gold_s, data_m = _build_three_layer_data_model(mapping)
    (ds_reg / "raw_schema.yaml").write_text(yaml.safe_dump(raw_s.model_dump(), sort_keys=False), encoding="utf-8")
    (ds_reg / "staging_schema.yaml").write_text(yaml.safe_dump(stage_s.model_dump(), sort_keys=False), encoding="utf-8")
    (ds_reg / "gold_schema.yaml").write_text(yaml.safe_dump(gold_s.model_dump(), sort_keys=False), encoding="utf-8")
    (ds_reg / "data_model.yaml").write_text(yaml.safe_dump(data_m.model_dump(), sort_keys=False), encoding="utf-8")

    # Recompile all DDLs
    run_ddl_generator_agent(dataset, REGISTRY_ROOT)

    # Re-export semantic artifacts
    em = build_entity_model(mapping)
    export_dbt_project(em, ds_reg / "dbt")
    export_openapi_spec(em, ds_reg / "openapi.json")
    export_json_schema(em, ds_reg / "openapi.json_schema.json")

    return JSONResponse(
        {
            "ok": True,
            "entity_name": entity_name,
            "version": mapping.version,
            "added_fields": added_fields,
            "state": _get_dataset_state(dataset),
        }
    )


async def api_get_alerts(request: Request) -> JSONResponse:
    """Retrieve recent alerts from the dataset's persistent alert_history.jsonl."""
    dataset = request.query_params.get("dataset", "analytics")
    ds_reg = REGISTRY_ROOT / dataset
    history_file = ds_reg / "alert_history.jsonl"
    alerts = []
    if history_file.exists():
        try:
            for line in history_file.read_text(encoding="utf-8").strip().splitlines():
                if line.strip():
                    alerts.append(json.loads(line))
        except Exception:
            pass
    alerts.reverse()  # most recent first
    return JSONResponse({"ok": True, "dataset": dataset, "alerts": alerts, "count": len(alerts)})


async def api_send_test_alert(request: Request) -> JSONResponse:
    """Dispatches a test alert notification to test multi-channel webhook formatting."""
    body = await request.json()
    dataset = body.get("dataset", "analytics")
    severity = body.get("severity", "HIGH")
    notif = AlertNotification(
        dataset=dataset,
        event_type="GATE_FAILURE",
        severity=severity,
        title=f"Test Connectivity Alert: `{dataset}`",
        summary=f"This is an automated test alert triggered from the Control Plane UI at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}.",
        details={"origin": "Control_Plane_UI_Test", "triggered_by": "data_steward"},
    )
    res = dispatch_alert(notif, dry_run=True, registry_root=REGISTRY_ROOT)
    return JSONResponse({"ok": True, "dataset": dataset, "result": res})


async def api_export_dbt(request: Request) -> JSONResponse:
    dataset = request.query_params.get("dataset", "analytics")
    ds_reg = REGISTRY_ROOT / dataset
    mapping_data = _load_yaml(ds_reg / "mapping.yaml")
    if not mapping_data:
        return JSONResponse({"ok": False, "error": f"No mapping found for dataset {dataset}"}, status_code=404)
    em = build_entity_model(DatasetMapping.model_validate(mapping_data))
    dbt_out = ds_reg / "dbt"
    res = export_dbt_project(em, dbt_out)
    return JSONResponse({"ok": True, "dataset": dataset, **res})


async def api_export_openapi(request: Request) -> JSONResponse:
    dataset = request.query_params.get("dataset", "analytics")
    ds_reg = REGISTRY_ROOT / dataset
    mapping_data = _load_yaml(ds_reg / "mapping.yaml")
    if not mapping_data:
        return JSONResponse({"ok": False, "error": f"No mapping found for dataset {dataset}"}, status_code=404)
    em = build_entity_model(DatasetMapping.model_validate(mapping_data))
    spec_path = ds_reg / "openapi.json"
    spec = export_openapi_spec(em, spec_path)
    return JSONResponse(spec)


async def api_export_json_schema(request: Request) -> JSONResponse:
    dataset = request.query_params.get("dataset", "analytics")
    ds_reg = REGISTRY_ROOT / dataset
    mapping_data = _load_yaml(ds_reg / "mapping.yaml")
    if not mapping_data:
        return JSONResponse({"ok": False, "error": f"No mapping found for dataset {dataset}"}, status_code=404)
    em = build_entity_model(DatasetMapping.model_validate(mapping_data))
    schema_path = ds_reg / "schema.json"
    schema = export_json_schema(em, schema_path)
    return JSONResponse(schema)


async def api_audit_hierarchy(request: Request) -> JSONResponse:
    dataset = request.query_params.get("dataset", "analytics")
    file_param = request.query_params.get("file")
    if file_param:
        target_file = BASE_DIR / file_param
    else:
        manifest = _load_yaml(REGISTRY_ROOT / dataset / "onboarding_manifest.yaml")
        sample_dir = Path(manifest.get("onboarding_sample_dir", "")) if manifest else Path()
        sample_files = manifest.get("valid_sample_files", []) if manifest else []
        target_file = sample_dir / sample_files[0] if sample_files else None

    if not target_file or not target_file.exists():
        return JSONResponse({"ok": False, "error": "Target XML file not found"}, status_code=404)

    audit_res = audit_xml_hierarchical_integrity(target_file)
    return JSONResponse({"ok": True, "dataset": dataset, "audit": audit_res})


async def api_export_dq_certificate(request: Request) -> HTMLResponse:
    dataset = request.query_params.get("dataset", "analytics")
    manifest = _load_yaml(REGISTRY_ROOT / dataset / "onboarding_manifest.yaml")
    sample_dir = Path(manifest.get("onboarding_sample_dir", "")) if manifest else Path()
    sample_files = manifest.get("valid_sample_files", []) if manifest else []
    target_file = sample_dir / sample_files[0] if sample_files else None

    if not target_file or not target_file.exists():
        return HTMLResponse("<h1>Target XML file not found</h1>", status_code=404)

    cert_res = generate_compliance_certificate(dataset, target_file, REGISTRY_ROOT)
    html_file = Path(cert_res["output_html"])
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


async def api_export_changelog(request: Request) -> HTMLResponse:
    dataset = request.query_params.get("dataset", "analytics")
    ds_reg = REGISTRY_ROOT / dataset
    mapping_data = _load_yaml(ds_reg / "mapping.yaml")
    if not mapping_data:
        return HTMLResponse("<h1>No mapping found for dataset</h1>", status_code=404)
    base_m = DatasetMapping.model_validate(mapping_data)
    diff = compare_mappings(base_m, base_m)
    md = generate_changelog_markdown(diff)

    # Wrap in clean HTML viewer
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Schema Evolution Changelog — {dataset.upper()}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; max-width: 900px; margin: 0 auto; line-height: 1.6; }}
    pre {{ background: #1e293b; padding: 18px; border-radius: 10px; border: 1px solid #334155; overflow-x: auto; font-size: 13px; color: #38bdf8; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    th, td {{ border: 1px solid #334155; padding: 10px 14px; text-align: left; font-size: 13px; }}
    th {{ background: #1e293b; color: #94a3b8; }}
    h1, h2 {{ border-bottom: 1px solid #334155; padding-bottom: 8px; color: #f8fafc; }}
    code {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #a5b4fc; font-size: 13px; }}
  </style>
</head>
<body>
  <pre>{md}</pre>
</body>
</html>"""
    return HTMLResponse(html)


routes = [
    Route("/", index_page, methods=["GET"]),
    Route("/api/state", api_list_datasets, methods=["GET"]),
    Route("/api/llm-config", api_configure_llm, methods=["POST"]),
    Route("/api/snowflake-config", api_configure_snowflake, methods=["POST"]),
    Route("/api/bootstrap", api_bootstrap, methods=["POST"]),
    Route("/api/save-schema", api_save_schema_overrides, methods=["POST"]),
    Route("/api/approve-yamls", api_approve_yamls_and_generate_ddl, methods=["POST"]),
    Route("/api/provision", api_approve_schema_and_provision, methods=["POST"]),
    Route("/api/go-live", api_approve_go_live, methods=["POST"]),
    Route("/api/ingest", api_ingest_xml, methods=["POST"]),
    Route("/api/replay-quarantine", api_replay_quarantine, methods=["POST"]),
    Route("/api/approve-child-entity", api_approve_child_entity, methods=["POST"]),
    Route("/api/alerts", api_get_alerts, methods=["GET"]),
    Route("/api/alerts/test", api_send_test_alert, methods=["POST"]),
    Route("/api/export/dbt", api_export_dbt, methods=["GET", "POST"]),
    Route("/api/export/openapi", api_export_openapi, methods=["GET"]),
    Route("/api/export/json-schema", api_export_json_schema, methods=["GET"]),
    Route("/api/export/dq-certificate", api_export_dq_certificate, methods=["GET"]),
    Route("/api/export/changelog", api_export_changelog, methods=["GET"]),
    Route("/api/audit-hierarchy", api_audit_hierarchy, methods=["GET"]),
]

app = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
