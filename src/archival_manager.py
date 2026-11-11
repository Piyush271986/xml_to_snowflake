"""Automated Lifecycle and GZIP Archival Manager for Ingested XML Feeds."""
from __future__ import annotations

import gzip
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def archive_ingested_file(
    xml_file: Path,
    archive_root: Path,
    dataset: str,
) -> dict[str, Any]:
    """Compresses an ingested XML file with GZIP and moves it to a year/month partition directory."""
    raw_bytes = xml_file.read_bytes()
    file_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    now = datetime.now(timezone.utc)
    year_month = now.strftime("%Y/%m")
    dest_dir = archive_root / dataset / year_month
    dest_dir.mkdir(parents=True, exist_ok=True)

    gz_filename = f"{xml_file.stem}_{now.strftime('%Y%m%d_%H%M%S')}.xml.gz"
    gz_path = dest_dir / gz_filename

    # Write compressed GZIP
    with gzip.open(gz_path, "wb") as gz_out:
        gz_out.write(raw_bytes)

    orig_size_bytes = len(raw_bytes)
    compressed_size_bytes = gz_path.stat().st_size
    compression_ratio = round((1 - (compressed_size_bytes / orig_size_bytes)) * 100, 1) if orig_size_bytes else 0

    manifest = {
        "dataset": dataset,
        "original_file": xml_file.name,
        "original_size_bytes": orig_size_bytes,
        "compressed_file": gz_filename,
        "compressed_path": str(gz_path),
        "compressed_size_bytes": compressed_size_bytes,
        "compression_savings_pct": compression_ratio,
        "file_sha256": file_sha256,
        "archived_at": now.isoformat(),
    }

    manifest_path = dest_dir / f"{xml_file.stem}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest
