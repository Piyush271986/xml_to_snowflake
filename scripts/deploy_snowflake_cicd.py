"""CLI Deployment Script for CI/CD Automated Pipelines.

Executes Step 3 live deployment against Snowflake without requiring browser SSO.
Used by GitHub Actions / GitLab CI / Azure DevOps runners.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.snowflake_client import (
    deploy_pipeline_to_snowflake_external_browser as deploy_dataset_to_snowflake,
    get_snowflake_status,
    load_snowflake_config,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless CI/CD Snowflake Deployment Runner")
    parser.add_argument("--dataset", default="analytics", help="Dataset name in registry/")
    parser.add_argument(
        "--registry-root",
        default="registry",
        help="Path to the dataset registry root (default: registry)",
    )
    parser.add_argument(
        "--skip-samples",
        action="store_true",
        help="Do not seed sample XML files into RAW schema during deployment",
    )
    parser.add_argument(
        "--enable-snowpipe",
        action="store_true",
        help="Unpause production Snowpipe on deployment (Go-Live)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate connection and configuration only without executing DDLs",
    )

    args = parser.parse_args()

    cfg = load_snowflake_config()
    print("=" * 60)
    print("Snowflake CI/CD Deployment Runner")
    print("=" * 60)
    print(f"Target Database   : {cfg.database}")
    print(f"Target Warehouse  : {cfg.warehouse}")
    print(f"Target Role       : {cfg.role}")
    print(f"Target Account    : {cfg.account}")
    print(f"Target User       : {cfg.user}")
    print(f"Authenticator     : {cfg.authenticator}")
    print(f"Dataset           : {args.dataset}")
    print(f"Enable Snowpipe   : {args.enable_snowpipe}")
    print(f"Seed Samples      : {not args.skip_samples}")
    print("=" * 60)

    if args.dry_run:
        print("[DRY-RUN] Checking connection status...")
        status = get_snowflake_status()
        print(json.dumps(status, indent=2))
        return 0

    registry_path = Path(args.registry_root).resolve()
    if not (registry_path / args.dataset).exists():
        print(f"[ERROR] Dataset '{args.dataset}' does not exist in {registry_path}", file=sys.stderr)
        return 1

    try:
        print(f"Deploying dataset '{args.dataset}' to Snowflake...")
        report = deploy_dataset_to_snowflake(
            dataset=args.dataset,
            registry_root=registry_path,
            seed_samples=not args.skip_samples,
            enable_snowpipe=args.enable_snowpipe,
            cfg=cfg,
        )
        print("\n[SUCCESS] Deployment completed successfully!")
        print(f"  Statements Executed : {report.get('statements_executed', 0)}")
        print(f"  Statements Succeeded: {report.get('statements_succeeded', 0)}")
        print(f"  Statements Warnings : {report.get('statements_warnings', 0)}")
        print(f"  Snowpipe Enabled    : {report.get('snowpipe_enabled', False)}")
        return 0
    except Exception as exc:
        print(f"\n[FATAL] Deployment failed with error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
