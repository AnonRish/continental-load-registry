#!/usr/bin/env python3
"""Record the latest successful public captures in data/source_manifest.json.

Two different things are described per source and must never be mixed:

* ``capture_*`` / ``source_*`` -- the bytes the core registry rows were built
  from. Facility records cite these. They change only when those rows are
  re-captured, so this script never writes them.
* ``latest_public_snapshot`` / ``latest_raw_capture`` -- the most recent
  successful run of the daily complete-queue or raw-page adapters. These are
  separate, non-additive layers and are refreshed here.

The script never invents a capture date: a failed source updates only its
last-attempt fields, and the last successful capture stays as it was.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

QUEUE_SNAPSHOTS = {
    "CAISO": ("caiso_public_queue_summary.json", "caiso_public_queue.json"),
    "MISO": ("miso_public_queue_summary.json", "miso_public_queue.json"),
    "SPP": ("spp_public_queue_summary.json", "spp_public_queue.json"),
    "PJM": ("pjm_cycle_public_queue_summary.json", "pjm_cycle_public_queue.json"),
}
RAW_CAPTURE_IDS = {"ERCOT-GIS": "ERCOT", "ISO-NE": "ISO-NE", "IESO": "IESO", "AESO": "AESO"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def parse_auxiliary(stdout: str) -> list[dict]:
    try:
        obj = json.loads(stdout)
    except (TypeError, ValueError):
        return []
    return obj.get("sources", []) if isinstance(obj, dict) else []


def main() -> None:
    manifest_path = DATA / "source_manifest.json"
    manifest = load(manifest_path)
    sources = manifest.setdefault("sources", {})
    updated: list[str] = []

    for key, (summary_name, snapshot_name) in QUEUE_SNAPSHOTS.items():
        summary_path = DATA / summary_name
        if not summary_path.exists():
            continue
        captured = load(summary_path).get("captured_at")
        if not captured:
            continue
        sources.setdefault(key, {})["latest_public_snapshot"] = {
            "captured_at": captured,
            "file": f"data/{snapshot_name}",
            "sha256": file_sha(DATA / snapshot_name),
            "basis": "Latest successful complete public queue snapshot (non-additive layer; not the core registry rows).",
        }
        updated.append(key)

    nyiso_status = DATA / "nyiso_public_queue_status.json"
    if nyiso_status.exists():
        obj = load(nyiso_status)
        rec = sources.setdefault("NYISO", {})
        rec["last_attempt_at"] = obj.get("captured_at")
        rec["last_attempt_status"] = obj.get("status")

    report_path = DATA / "automation" / "adapter_run_report.json"
    if report_path.exists():
        for run in load(report_path).get("runs", []):
            if run.get("source") != "ERCOT / ISO-NE / IESO / AESO raw source capture":
                continue
            for item in parse_auxiliary(run.get("stdout_tail", "")):
                key = RAW_CAPTURE_IDS.get(item.get("source_id", ""))
                if not key or item.get("status") != "RAW_CAPTURED":
                    continue
                sources.setdefault(key, {})["latest_raw_capture"] = {
                    "captured_at": item.get("captured_at_utc"),
                    "file": item.get("path") or item.get("raw_capture"),
                    "sha256": item.get("sha256"),
                    "basis": "Latest successful raw publisher page/file capture (not the core registry rows).",
                }
                updated.append(key)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest["generated_on"] = now
    manifest["last_metadata_refresh_utc"] = now
    manifest["metadata_refresh_policy"] = (
        "capture_* and source_* fields describe the bytes the core registry rows came from and change only "
        "when those rows are re-captured. The daily complete-queue and raw-page captures are recorded "
        "separately under latest_public_snapshot / latest_raw_capture."
    )
    manifest["metadata_refresh_updated_sources"] = sorted(set(updated))
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"updated_sources": sorted(set(updated)), "generated_on": now}, indent=2))


if __name__ == "__main__":
    main()
