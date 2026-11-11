"""Enterprise Alerting and Notification Dispatcher for Data Quality and Schema Drift."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
import urllib.request


@dataclass
class AlertNotification:
    dataset: str
    event_type: Literal[
        "BREAKING_DRIFT",
        "ADDITIVE_DRIFT",
        "DQ_FAILURE",
        "QUARANTINE_SPIKE",
        "GATE_FAILURE",
        "RECONCILIATION_MISMATCH",
        "CARDINALITY_VIOLATION",
    ]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "INFO"]
    title: str
    summary: str
    details: dict[str, Any]
    owner: str = "data-steward@enterprise.io"


def build_reconciliation_alert(dataset: str, recon_audit: dict[str, Any]) -> AlertNotification:
    """Builds an alert when zero-loss reconciliation detects a discrepancy delta."""
    metrics = recon_audit.get("metrics", {})
    delta = metrics.get("discrepancy_delta", 0)
    return AlertNotification(
        dataset=dataset,
        event_type="RECONCILIATION_MISMATCH",
        severity="CRITICAL" if abs(delta) > 0 else "INFO",
        title=f"Data Reconciliation Mismatch (Delta = {delta}) in `{dataset}`",
        summary=f"Reconciliation check failed: Source records ({metrics.get('source_assets')}) does not balance with Curated ({metrics.get('curated_assets')}) + Quarantined ({metrics.get('quarantined_assets')}). Discrepancy delta = {delta}.",
        details=recon_audit,
    )


def build_cardinality_alert(dataset: str, dq_audit: dict[str, Any]) -> AlertNotification:
    """Builds an alert when repeating child set sizes do not match expected @SIZE."""
    discrepancies = dq_audit.get("size_discrepancies", 0)
    return AlertNotification(
        dataset=dataset,
        event_type="CARDINALITY_VIOLATION",
        severity="HIGH" if discrepancies > 0 else "INFO",
        title=f"Hierarchical Set Cardinality Violations ({discrepancies}) in `{dataset}`",
        summary=f"Audit revealed {discrepancies} instances where repeating child records count did not match container @SIZE attribute in {dq_audit.get('xml_file', 'feed')}.",
        details={
            "size_discrepancies": discrepancies,
            "error_count": dq_audit.get("error_count", 0),
            "warning_count": dq_audit.get("warning_count", 0),
            "findings_sample": dq_audit.get("findings_sample", [])[:5],
        },
    )


def build_drift_alert(dataset: str, proposal_status: str, findings_count: int, file_name: str) -> AlertNotification:
    """Builds an alert for newly detected schema drift."""
    is_breaking = proposal_status == "BREAKING_HELD_FOR_APPROVAL"
    return AlertNotification(
        dataset=dataset,
        event_type="BREAKING_DRIFT" if is_breaking else "ADDITIVE_DRIFT",
        severity="HIGH" if is_breaking else "INFO",
        title=f"Schema Drift Detected ({proposal_status}) in `{file_name}`",
        summary=f"Drift agent identified {findings_count} unexpected structural or type changes in {file_name}. Status: {proposal_status}.",
        details={"file": file_name, "proposal_status": proposal_status, "findings_count": findings_count},
    )


def format_slack_blocks(notification: AlertNotification) -> dict[str, Any]:
    """Formats Slack Blocks payload."""
    severity_emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "🔔", "INFO": "ℹ️"}.get(notification.severity, "ℹ️")
    return {
        "text": f"[{notification.severity}] {notification.title}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{severity_emoji} {notification.title}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Dataset:*\n`{notification.dataset}`"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n`{notification.severity}`"},
                    {"type": "mrkdwn", "text": f"*Event Type:*\n`{notification.event_type}`"},
                    {"type": "mrkdwn", "text": f"*Owner:*\n<{notification.owner}>"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Summary:*\n{notification.summary}"},
            },
        ],
    }


def format_teams_card(notification: AlertNotification) -> dict[str, Any]:
    """Formats Microsoft Teams Adaptive Card payload."""
    theme_color = {"CRITICAL": "d9534f", "HIGH": "f0ad4e", "MEDIUM": "0275d8", "INFO": "5cb85c"}.get(
        notification.severity, "0275d8"
    )
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": theme_color,
        "summary": notification.title,
        "sections": [
            {
                "activityTitle": f"[{notification.severity}] {notification.title}",
                "activitySubtitle": f"Dataset: {notification.dataset} | Type: {notification.event_type}",
                "facts": [
                    {"name": "Dataset", "value": notification.dataset},
                    {"name": "Severity", "value": notification.severity},
                    {"name": "Owner", "value": notification.owner},
                ],
                "text": notification.summary,
            }
        ],
    }


def format_pagerduty_payload(notification: AlertNotification) -> dict[str, Any]:
    """Formats PagerDuty Events API v2 payload."""
    severity_map = {"CRITICAL": "critical", "HIGH": "error", "MEDIUM": "warning", "INFO": "info"}
    return {
        "routing_key": os.environ.get("PAGERDUTY_ROUTING_KEY", "mock-routing-key"),
        "event_action": "trigger",
        "payload": {
            "summary": f"[{notification.severity}] {notification.title}: {notification.summary}",
            "source": f"pipeline-agent/{notification.dataset}",
            "severity": severity_map.get(notification.severity, "warning"),
            "component": "XML_Data_Lakehouse",
            "group": notification.dataset,
            "custom_details": notification.details,
        },
    }


def log_alert_history(dataset: str, payload: dict[str, Any], registry_root: Path | None = None) -> None:
    """Appends an alert to the dataset's local audit history log."""
    if registry_root is None:
        registry_root = Path("registry")
    ds_dir = registry_root / dataset
    if ds_dir.exists():
        log_file = ds_dir / "alert_history.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")


def dispatch_alert(
    notification: AlertNotification,
    dry_run: bool = True,
    registry_root: Path | None = None,
) -> dict[str, Any]:
    """Dispatches a structured alert to Slack, Teams, or PagerDuty and logs to history."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": notification.dataset,
        "event_type": notification.event_type,
        "severity": notification.severity,
        "title": notification.title,
        "summary": notification.summary,
        "owner": notification.owner,
        "details": notification.details,
        "slack_payload": format_slack_blocks(notification),
        "teams_payload": format_teams_card(notification),
        "pagerduty_payload": format_pagerduty_payload(notification),
    }

    # Record in local persistent log
    log_alert_history(notification.dataset, payload, registry_root)

    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    status_code: Any = "DRY_RUN_DISPATCHED"

    if not dry_run and slack_webhook:
        try:
            req = urllib.request.Request(
                slack_webhook,
                data=json.dumps(payload["slack_payload"]).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                status_code = resp.status
        except Exception as e:
            status_code = f"ERROR: {e}"

    return {
        "status": "SENT" if status_code == 200 or dry_run else "FAILED",
        "dispatch_code": status_code,
        "payload": payload,
    }
