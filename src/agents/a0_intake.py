"""Stage 1 — A0: Intake Agent.

Validates the onboarding request, checks sample XML files exist, separates malformed files,
creates the C4 registry directory, and initializes a DRAFT DataHub stub.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.models import OnboardingManifest


def run_a0_intake(
    dataset: str,
    source_system: str,
    sample_dir: Path,
    registry_root: Path,
    adls_landing_path: str,
    data_steward: str = "data-steward@enterprise.io",
    engineering_owner: str = "data-eng@enterprise.io",
    freshness_sla_hours: int = 24,
) -> OnboardingManifest:
    """Execute A0 Intake checks and write onboarding_manifest.yaml."""
    if not sample_dir.exists() or not sample_dir.is_dir():
        raise FileNotFoundError(f"A0 Intake failed: sample directory does not exist: {sample_dir}")

    xml_candidates = sorted(sample_dir.glob("*.xml"))
    if not xml_candidates:
        raise ValueError(f"A0 Intake failed: no .xml sample files found in {sample_dir}")

    valid_files: list[str] = []
    quarantined_files: list[str] = []
    for p in xml_candidates:
        try:
            ET.parse(p)
            valid_files.append(p.name)
        except ET.ParseError:
            quarantined_files.append(p.name)

    if not valid_files:
        raise ValueError("A0 Intake failed: all sample XML files are malformed.")

    ds_registry = registry_root / dataset
    ds_registry.mkdir(parents=True, exist_ok=True)

    manifest = OnboardingManifest(
        dataset=dataset,
        source_system=source_system,
        adls_landing_path=adls_landing_path,
        onboarding_sample_dir=str(sample_dir),
        data_steward=data_steward,
        engineering_owner=engineering_owner,
        freshness_sla_hours=freshness_sla_hours,
        valid_sample_files=valid_files,
        quarantined_sample_files=quarantined_files,
        status="DRAFT",
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    manifest_path = ds_registry / "onboarding_manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest.model_dump(), sort_keys=False),
        encoding="utf-8",
    )

    # Create initial DataHub DRAFT stub
    stub_path = ds_registry / "datahub_stub.yaml"
    stub_path.write_text(
        yaml.safe_dump(
            {
                "urn": f"urn:li:dataset:(urn:li:dataPlatform:snowflake,{dataset},PROD)",
                "status": "DRAFT",
                "owners": [data_steward, engineering_owner],
                "created_by": "A0_Intake_Agent",
                "created_at": manifest.created_at,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return manifest
