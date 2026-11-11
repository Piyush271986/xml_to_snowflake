"""Enterprise Alerting and Notification Dispatcher for Data Quality and Schema Drift."""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal


@dataclass
class AlertNotification:
    dataset: str
    event_type: Literal["BREAKING_DRIFT", "ADDITIVE_DRIFT", "DQ_FAILURE", "QUARANTINE_SPIKE", "GATE_FAILURE"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "INFO"]
    title: str
    summary: str
    details: dict[str, Any]
    owner: str = "data-steward@enterprise.io"


def dispatch_alert(notification: AlertNotification, dry_run: bool = True) -> dict[str, Any]:
    """Dispatches a structured alert to configured webhook endpoints (Slack, Teams, etc.)."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": notification.dataset,
        "event_type": notification.event_type,
        "severity": notification.severity,
        "title": notification.title,
        "summary": notification.summary,
        "owner": notification.owner,
        "details": notification.details,
    }

    # Format Slack Blocks message
    slack_blocks = {
        "text": f"[{notification.severity}] {notification.title}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 {notification.title}"},
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

    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")

    if not dry_run and slack_webhook:
        try:
            req = urllib.request.Request(
                slack_webhook,
                data=json.dumps(slack_blocks).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                status_code = resp.status
        except Exception as e:
            status_code = f"ERROR: {e}"
    else:
        status_code = "DRY_RUN_DISPATCHED"

    return {
        "status": "SENT" if status_code == 200 or dry_run else "FAILED",
        "dispatch_code": status_code,
        "payload": payload,
    }
