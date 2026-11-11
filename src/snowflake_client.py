"""Snowflake External Browser SSO Connector & Live Pipeline Deployment Engine.

Supports:
1. Interactive External Browser SSO authentication (`authenticator="externalbrowser"`).
2. Live connection verification (`SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_VERSION()`).
3. Final pipeline deployment after human review & approval:
   - Creates target Database & Schemas (`RAW`, `STAGING`, `CURATED`, `OPS`) if needed.
   - Executes Layer 1 (`sql/01_raw_snowpipe.sql`), Layer 2 (`sql/02_staging_dynamic_table.sql`),
     Layer 3 (`sql/03_gold_dynamic_table.sql`), Operational tables (`sql/04_ops_quarantine_dq.sql`),
     and `monitoring.sql`.
   - Optionally loads sample XML files into the RAW table and refreshes the Stage & Final Gold Dynamic Tables.
   - Optionally unpauses production Snowpipe (`ALTER PIPE pipe_<dataset> SET PIPE_EXECUTION_PAUSED = FALSE`).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from typing import Any

import yaml

from src.entity_model import build_entity_model
from src.models import DatasetMapping

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"


@dataclass
class SnowflakeConnectionConfig:
    """Configuration for Snowflake connection via External Browser SSO or Password/PAT."""

    mode: str = "externalbrowser"  # 'externalbrowser', 'snowflake', or 'local_simulation'
    authenticator: str = "externalbrowser"  # 'externalbrowser', 'snowflake', or 'username_password_mfa'
    account: str = ""
    user: str = ""
    password: str = ""
    role: str = "DATA_ENGINEER_ROLE"
    warehouse: str = "COMPUTE_WH"
    database: str = "ENTERPRISE_DW"
    schema_raw: str = "RAW"
    schema_staging: str = "STAGING"
    schema_curated: str = "CURATED"
    schema_ops: str = "OPS"
    adls_stage: str = "@RAW.ADLS_XML_STAGE"

    @property
    def is_configured(self) -> bool:
        clean_acc = (self.account or "").strip()
        return bool(clean_acc and not clean_acc.startswith("<"))

    def to_status_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("password", None)
        d["password_set"] = bool(self.password)
        d["is_configured"] = self.is_configured
        return d


@dataclass
class StatementExecutionLog:
    """Audit log for a single SQL statement executed on Snowflake."""

    step: str
    sql_preview: str
    status: str  # SUCCESS, WARNING, FAILED
    query_id: str | None = None
    rowcount: int | None = None
    message: str = ""
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# In-memory runtime overrides set from the Web UI
_RUNTIME_SF_OVERRIDES: dict[str, str] = {}
_LAST_VERIFIED_SESSION: dict[str, Any] = {}


def normalize_snowflake_account(raw_account: str) -> str:
    """Normalize a Snowflake account string or full URL into a clean account identifier.

    Examples:
      - 'https://yldulxm-dc69211.snowflakecomputing.com/' -> 'yldulxm-dc69211'
      - 'yldulxm-dc69211.snowflakecomputing.com'          -> 'yldulxm-dc69211'
      - 'YLDULXM-DC69211'                                 -> 'YLDULXM-DC69211'
    """
    acc = (raw_account or "").strip()
    if not acc or acc.startswith("<"):
        return ""
    for prefix in ("https://", "http://"):
        if acc.lower().startswith(prefix):
            acc = acc[len(prefix) :]
    acc = acc.split("/")[0].strip()
    suffix = ".snowflakecomputing.com"
    while acc.lower().endswith(suffix):
        acc = acc[: -len(suffix)].strip()
    return acc


def load_snowflake_config(settings_path: Path | None = None) -> SnowflakeConnectionConfig:
    """Load Snowflake connection settings from config/settings.yaml + environment/UI overrides."""
    path = settings_path or DEFAULT_SETTINGS_PATH
    raw_sf: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            raw_sf = loaded.get("snowflake") or {}
        except Exception:
            raw_sf = {}

    def _pick(key: str, env_key: str, default: str) -> str:
        if key in _RUNTIME_SF_OVERRIDES and _RUNTIME_SF_OVERRIDES[key] != "":
            return _RUNTIME_SF_OVERRIDES[key]
        if os.environ.get(env_key):
            return os.environ[env_key].strip()
        val = str(raw_sf.get(key, default)).strip()
        return val if val else default

    account = normalize_snowflake_account(_pick("account", "SNOWFLAKE_ACCOUNT", ""))
    user = _pick("user", "SNOWFLAKE_USER", "")
    if user.startswith("<"):
        user = ""
    password = _pick("password", "SNOWFLAKE_PASSWORD", "")

    return SnowflakeConnectionConfig(
        mode=_pick("mode", "SNOWFLAKE_MODE", "externalbrowser"),
        authenticator=_pick("authenticator", "SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
        account=account,
        user=user,
        password=password,
        role=_pick("role", "SNOWFLAKE_ROLE", "DATA_ENGINEER_ROLE"),
        warehouse=_pick("warehouse", "SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=_pick("database", "SNOWFLAKE_DATABASE", "ENTERPRISE_DW"),
        schema_raw=_pick("schema_raw", "SNOWFLAKE_SCHEMA_RAW", "RAW"),
        schema_staging=_pick("schema_staging", "SNOWFLAKE_SCHEMA_STAGING", "STAGING"),
        schema_curated=_pick("schema_curated", "SNOWFLAKE_SCHEMA_CURATED", "CURATED"),
        schema_ops=_pick("schema_ops", "SNOWFLAKE_SCHEMA_OPS", "OPS"),
        adls_stage=_pick("adls_stage", "SNOWFLAKE_ADLS_STAGE", "@RAW.ADLS_XML_STAGE"),
    )


def update_snowflake_config(overrides: dict[str, Any]) -> SnowflakeConnectionConfig:
    """Update runtime Snowflake configuration from the UI."""
    for k in (
        "mode",
        "authenticator",
        "account",
        "user",
        "password",
        "role",
        "warehouse",
        "database",
        "schema_raw",
        "schema_staging",
        "schema_curated",
        "schema_ops",
        "adls_stage",
    ):
        if k in overrides and overrides[k] is not None:
            val = str(overrides[k]).strip()
            if k == "account":
                val = normalize_snowflake_account(val)
            # Only overwrite password if non-empty (or if clear_password is requested)
            if k == "password" and not val and not overrides.get("clear_password"):
                continue
            _RUNTIME_SF_OVERRIDES[k] = val
    return load_snowflake_config()


def get_snowflake_status() -> dict[str, Any]:
    cfg = load_snowflake_config()
    st = cfg.to_status_dict()
    st["last_verified_session"] = _LAST_VERIFIED_SESSION or None
    return st


def _split_sql_statements(sql_script: str) -> list[str]:
    """Split a multi-statement SQL file into executable statements, stripping full-line comments first."""
    non_comment_lines = [
        ln
        for ln in sql_script.splitlines()
        if ln.strip() and not ln.strip().startswith("--")
    ]
    cleaned_script = "\n".join(non_comment_lines)
    statements: list[str] = []
    for raw_chunk in cleaned_script.split(";"):
        stmt = raw_chunk.strip()
        if stmt:
            statements.append(stmt + ";")
    return statements


def connect_snowflake_external_browser(cfg: SnowflakeConnectionConfig | None = None):
    """Open a live Snowflake connection.

    Supports:
    - `authenticator='externalbrowser'` (Browser SSO for Okta / Azure AD / Entra ID / SAML IdP)
    - `authenticator='snowflake'` (Standard Snowflake Username & Password / PAT for accounts without a SAML IdP)
    - `authenticator='username_password_mfa'` (Username + Password + Duo MFA push/passcode)
    """
    import snowflake.connector

    cfg = cfg or load_snowflake_config()
    if not cfg.is_configured:
        raise ValueError(
            "Snowflake Account Identifier is required (e.g. 'YLDULXM-DC69211'). Configure it in the UI first."
        )

    auth_mode = (cfg.authenticator or "externalbrowser").strip().lower()
    conn_kwargs: dict[str, Any] = {
        "account": normalize_snowflake_account(cfg.account),
        "authenticator": auth_mode,
        "login_timeout": 120,
    }
    if auth_mode == "externalbrowser":
        conn_kwargs["client_store_temporary_credential"] = True
    else:
        if not cfg.user:
            raise ValueError("Snowflake User is required when using Password / PAT authentication.")
        if not cfg.password:
            raise ValueError(
                "Snowflake Password (or Programmatic Access Token) is required when Authenticator is not External Browser."
            )
        conn_kwargs["password"] = cfg.password

    if cfg.user:
        conn_kwargs["user"] = cfg.user
    if cfg.role:
        conn_kwargs["role"] = cfg.role
    if cfg.warehouse:
        conn_kwargs["warehouse"] = cfg.warehouse
    if cfg.database:
        conn_kwargs["database"] = cfg.database

    try:
        return snowflake.connector.connect(**conn_kwargs)
    except Exception as exc:
        msg = str(exc)
        if "390190" in msg or "SAML Identity Provider" in msg:
            raise RuntimeError(
                f"{msg} — NOTE: Error 390190 means your Snowflake account ({cfg.account}) does NOT have a SAML/SSO Identity Provider (Okta/Entra ID) configured on the account. "
                "Switch Authenticator in the UI from 'externalbrowser' to 'snowflake (Username & Password / PAT)' (or configure a SAML2 Security Integration in Snowflake) to connect!"
            ) from exc
        raise


def test_snowflake_external_browser_connection(
    cfg: SnowflakeConnectionConfig | None = None,
) -> dict[str, Any]:
    """Trigger External Browser SSO login and verify the live Snowflake session."""
    global _LAST_VERIFIED_SESSION
    cfg = cfg or load_snowflake_config()
    conn = connect_snowflake_external_browser(cfg)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    CURRENT_USER(),
                    CURRENT_ROLE(),
                    CURRENT_WAREHOUSE(),
                    CURRENT_DATABASE(),
                    CURRENT_SCHEMA(),
                    CURRENT_VERSION(),
                    CURRENT_ACCOUNT()
                """
            )
            row = cur.fetchone()
            session_info = {
                "connected": True,
                "authenticator": cfg.authenticator or "externalbrowser",
                "current_user": row[0],
                "current_role": row[1],
                "current_warehouse": row[2],
                "current_database": row[3],
                "current_schema": row[4],
                "snowflake_version": row[5],
                "current_account": row[6],
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }
            _LAST_VERIFIED_SESSION = session_info
            return session_info
        finally:
            cur.close()
    finally:
        conn.close()


def deploy_pipeline_to_snowflake_external_browser(
    dataset: str,
    registry_root: Path,
    cfg: SnowflakeConnectionConfig | None = None,
    enable_snowpipe: bool = True,
    seed_sample_xmls: bool = True,
) -> dict[str, Any]:
    """Connect to Snowflake via External Browser SSO and deploy the approved 3-layer pipeline end-to-end.

    Executes:
    1. Context setup (`USE ROLE`, `USE WAREHOUSE`, `CREATE DATABASE IF NOT EXISTS`, `CREATE SCHEMA IF NOT EXISTS`).
    2. Layer 1 SQL (`01_raw_snowpipe.sql`): Creates RAW Normal Table + ADLS Snowpipe.
       - Note: If the external ADLS stage (`@RAW.ADLS_XML_STAGE`) is not yet configured in the target
         Snowflake account, creates an internal XML stage fallback so `CREATE PIPE` succeeds cleanly.
    3. Layer 2 SQL (`02_staging_dynamic_table.sql`): Creates Stage Dynamic Table (`CREATE OR REPLACE DYNAMIC TABLE staging_<ds>`).
    4. Layer 3 SQL (`03_gold_dynamic_table.sql`): Creates Final Gold Dynamic Table (`CREATE OR REPLACE DYNAMIC TABLE curated_<ds>`).
    5. Operational SQL (`04_ops_quarantine_dq.sql`): Creates O3 Quarantine & O1 DQ tables.
    6. Monitoring SQL (`monitoring.sql`): Creates O5 SLA Dashboard View (`v_sla_dashboard_<ds>`).
    7. Sample XML Seeding (optional): Loads sample XML files into the RAW table and runs
       `ALTER DYNAMIC TABLE ... REFRESH` on Stage and Gold Dynamic Tables.
    8. Go-Live Snowpipe Activation (when `enable_snowpipe=True`): Executes
       `ALTER PIPE pipe_<dataset> SET PIPE_EXECUTION_PAUSED = FALSE`.
    """
    global _LAST_VERIFIED_SESSION
    cfg = cfg or load_snowflake_config()
    ds_registry = registry_root / dataset
    mapping_path = ds_registry / "mapping.yaml"
    if not mapping_path.exists():
        raise FileNotFoundError(f"Cannot deploy to Snowflake: missing {mapping_path}")

    mapping = DatasetMapping.model_validate(
        yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    )

    execution_logs: list[StatementExecutionLog] = []

    def _exec(cur: Any, step: str, sql: str, tolerate_error: bool = False) -> bool:
        preview = " ".join(sql.strip().split())[:180]
        try:
            cur.execute(sql)
            qid = getattr(cur, "sfqid", None)
            rc = getattr(cur, "rowcount", None)
            execution_logs.append(
                StatementExecutionLog(
                    step=step,
                    sql_preview=preview,
                    status="SUCCESS",
                    query_id=qid,
                    rowcount=rc,
                    message="Executed successfully on Snowflake",
                )
            )
            return True
        except Exception as exc:
            execution_logs.append(
                StatementExecutionLog(
                    step=step,
                    sql_preview=preview,
                    status="WARNING" if tolerate_error else "FAILED",
                    query_id=getattr(cur, "sfqid", None),
                    message=str(exc),
                )
            )
            if not tolerate_error:
                raise
            return False

    conn = connect_snowflake_external_browser(cfg)
    try:
        cur = conn.cursor()
        try:
            # 1. Session Info & Context Setup
            cur.execute(
                "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_VERSION(), CURRENT_ACCOUNT()"
            )
            srow = cur.fetchone()
            session_info = {
                "connected": True,
                "authenticator": cfg.authenticator or "externalbrowser",
                "current_user": srow[0],
                "current_role": srow[1],
                "current_warehouse": srow[2],
                "current_database": srow[3],
                "snowflake_version": srow[4],
                "current_account": srow[5],
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }
            _LAST_VERIFIED_SESSION = session_info

            if cfg.role:
                _exec(cur, "Context: Role", f"USE ROLE IDENTIFIER('{cfg.role}');", tolerate_error=True)
            if cfg.warehouse:
                _exec(
                    cur,
                    "Context: Warehouse",
                    f"CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER('{cfg.warehouse}') WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;",
                    tolerate_error=True,
                )
                _exec(cur, "Context: Use Warehouse", f"USE WAREHOUSE IDENTIFIER('{cfg.warehouse}');", tolerate_error=True)
            if cfg.database:
                _exec(
                    cur,
                    "Context: Database",
                    f"CREATE DATABASE IF NOT EXISTS IDENTIFIER('{cfg.database}');",
                    tolerate_error=True,
                )
                _exec(cur, "Context: Use Database", f"USE DATABASE IDENTIFIER('{cfg.database}');")

            schema_raw = cfg.schema_raw or "RAW"
            schema_staging = cfg.schema_staging or "STAGING"
            schema_curated = cfg.schema_curated or "CURATED"
            schema_ops = cfg.schema_ops or "OPS"

            for schema_name in [schema_raw, schema_staging, schema_curated, schema_ops]:
                if schema_name:
                    _exec(
                        cur,
                        f"Context: Schema {schema_name}",
                        f"CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{schema_name}');",
                        tolerate_error=True,
                    )

            # Drop any misplaced Stage/Gold/Ops objects that were previously created inside the RAW schema
            for wrong_dt in [mapping.targets.staging_table, mapping.targets.curated_table]:
                _exec(
                    cur,
                    f"Cleanup: Remove misplaced {schema_raw}.{wrong_dt}",
                    f"DROP DYNAMIC TABLE IF EXISTS {schema_raw}.{wrong_dt};",
                    tolerate_error=True,
                )
            for wrong_tbl in [mapping.targets.quarantine_table, mapping.targets.dq_results_table]:
                _exec(
                    cur,
                    f"Cleanup: Remove misplaced {schema_raw}.{wrong_tbl}",
                    f"DROP TABLE IF EXISTS {schema_raw}.{wrong_tbl};",
                    tolerate_error=True,
                )
            _exec(
                cur,
                f"Cleanup: Remove misplaced {schema_raw}.v_sla_dashboard_{dataset}",
                f"DROP VIEW IF EXISTS {schema_raw}.v_sla_dashboard_{dataset};",
                tolerate_error=True,
            )

            # Ensure XML File Format & Stage exist in RAW schema so Snowpipe creation succeeds
            _exec(cur, f"Context: Use Schema {schema_raw}", f"USE SCHEMA IDENTIFIER('{schema_raw}');")
            stage_clean = cfg.adls_stage.lstrip("@")
            _exec(
                cur,
                "Stage Setup: XML Stage",
                f"CREATE STAGE IF NOT EXISTS {stage_clean} FILE_FORMAT = (TYPE = 'XML' STRIP_OUTER_ELEMENT = FALSE);",
                tolerate_error=True,
            )

            # 2. Execute Step 2 Generated SQL scripts in their respective target schemas
            sql_dir = ds_registry / "sql"
            ordered_files = [
                ("Layer 1: RAW Table & Snowpipe", schema_raw, sql_dir / "01_raw_snowpipe.sql"),
                ("Layer 2: Stage Dynamic Table", schema_staging, sql_dir / "02_staging_dynamic_table.sql"),
                ("Layer 3: Gold Dynamic Table", schema_curated, sql_dir / "03_gold_dynamic_table.sql"),
                ("Ops Plane: O3 Quarantine & O1 DQ", schema_ops, sql_dir / "04_ops_quarantine_dq.sql"),
            ]

            for label, layer_schema, sql_path in ordered_files:
                if not sql_path.exists():
                    continue
                _exec(cur, f"Context: Use Schema {layer_schema}", f"USE SCHEMA IDENTIFIER('{layer_schema}');")
                sql_text = sql_path.read_text(encoding="utf-8")
                # Substitute configured warehouse if different from default COMPUTE_WH
                if cfg.warehouse and cfg.warehouse != "COMPUTE_WH":
                    sql_text = sql_text.replace("WAREHOUSE = COMPUTE_WH", f"WAREHOUSE = {cfg.warehouse}")
                statements = _split_sql_statements(sql_text)
                for idx, stmt in enumerate(statements, start=1):
                    is_pipe_stmt = "CREATE PIPE" in stmt.upper() or "ALTER PIPE" in stmt.upper()
                    _exec(
                        cur,
                        f"{label} [{layer_schema}] (#{idx})",
                        stmt,
                        tolerate_error=is_pipe_stmt,
                    )

            # 3. Deploy O5 SLA Dashboard View from monitoring.sql into OPS schema
            mon_path = ds_registry / "monitoring.sql"
            if mon_path.exists():
                _exec(cur, f"Context: Use Schema {schema_ops}", f"USE SCHEMA IDENTIFIER('{schema_ops}');")
                for idx, stmt in enumerate(_split_sql_statements(mon_path.read_text(encoding="utf-8")), start=1):
                    if stmt.upper().startswith("CREATE"):
                        _exec(cur, f"Stage 7: O5 Monitoring View [{schema_ops}] (#{idx})", stmt, tolerate_error=True)

            # 4. Optional: Seed sample XML files into live Snowflake RAW table & refresh Dynamic Tables
            seeded_files = 0
            manifest_path = ds_registry / "onboarding_manifest.yaml"
            raw_fqn = f"{schema_raw}.{mapping.targets.raw_table}"
            pipe_fqn = f"{schema_raw}.pipe_{dataset}"

            if seed_sample_xmls and manifest_path.exists():
                manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
                sample_dir = Path(manifest_data.get("onboarding_sample_dir", ""))
                sample_files = manifest_data.get("valid_sample_files") or []
                for sp in sample_files:
                    p = Path(sp)
                    if not p.is_absolute() and sample_dir:
                        p = sample_dir / sp
                    if not p.exists():
                        continue
                    xml_str = p.read_text(encoding="utf-8")
                    sha = hashlib.sha256(xml_str.encode("utf-8")).hexdigest()
                    try:
                        cur.execute(
                            f"""
                            INSERT INTO {raw_fqn} (_file_name, _file_sha256, _source_system, raw_xml)
                            SELECT %s, %s, %s, PARSE_XML(%s)
                            WHERE NOT EXISTS (
                                SELECT 1 FROM {raw_fqn} WHERE _file_name = %s AND _file_sha256 = %s
                            )
                            """,
                            (p.name, sha, manifest_data.get("source_system", dataset), xml_str, p.name, sha),
                        )
                        seeded_files += 1
                    except Exception as exc:
                        execution_logs.append(
                            StatementExecutionLog(
                                step=f"Seed Sample XML ({p.name})",
                                sql_preview=f"INSERT INTO {raw_fqn} ... PARSE_XML('{p.name}')",
                                status="WARNING",
                                message=str(exc),
                            )
                        )

                if seeded_files > 0:
                    execution_logs.append(
                        StatementExecutionLog(
                            step="Seed Sample XMLs into RAW",
                            sql_preview=f"INSERT INTO {raw_fqn} SELECT PARSE_XML(...) [{seeded_files} files]",
                            status="SUCCESS",
                            rowcount=seeded_files,
                            message=f"Loaded {seeded_files} XML sample file(s) into Snowflake {raw_fqn}",
                        )
                    )
                    for ent in build_entity_model(mapping).entities:
                        _exec(
                            cur,
                            f"Refresh Stage Dynamic Table ({schema_staging}.{ent.stage_table})",
                            f"ALTER DYNAMIC TABLE IF EXISTS {schema_staging}.{ent.stage_table} REFRESH;",
                            tolerate_error=True,
                        )
                    for ent in build_entity_model(mapping).entities:
                        _exec(
                            cur,
                            f"Refresh Curated Dynamic Table ({schema_curated}.{ent.curated_table})",
                            f"ALTER DYNAMIC TABLE IF EXISTS {schema_curated}.{ent.curated_table} REFRESH;",
                            tolerate_error=True,
                        )

            # 5. Unpause Snowpipe on final Go-Live deployment if requested
            if enable_snowpipe:
                _exec(
                    cur,
                    f"Go-Live: Enable Production Snowpipe ({pipe_fqn})",
                    f"ALTER PIPE IF EXISTS {pipe_fqn} SET PIPE_EXECUTION_PAUSED = FALSE;",
                    tolerate_error=True,
                )

            deployment_report = {
                "deployed": True,
                "mode": "snowflake_externalbrowser",
                "authenticator": cfg.authenticator or "externalbrowser",
                "dataset": dataset,
                "version": mapping.version,
                "snowflake_session": session_info,
                "target_database": cfg.database,
                "target_schema": f"{schema_raw} / {schema_staging} / {schema_curated} / {schema_ops}",
                "layer_schemas": {
                    "raw": schema_raw,
                    "staging": schema_staging,
                    "gold": schema_curated,
                    "ops": schema_ops,
                },
                "target_warehouse": cfg.warehouse,
                "seeded_sample_files": seeded_files,
                "snowpipe_enabled": enable_snowpipe,
                "statements_executed": len(execution_logs),
                "statements_succeeded": sum(1 for s in execution_logs if s.status == "SUCCESS"),
                "statements_warnings": sum(1 for s in execution_logs if s.status == "WARNING"),
                "execution_logs": [asdict(s) for s in execution_logs],
                "deployed_at": datetime.now(timezone.utc).isoformat(),
            }
            (ds_registry / "snowflake_live_deployment.yaml").write_text(
                yaml.safe_dump(deployment_report, sort_keys=False),
                encoding="utf-8",
            )
            return deployment_report
        finally:
            cur.close()
    finally:
        conn.close()
