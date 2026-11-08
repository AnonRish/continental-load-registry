#!/usr/bin/env python3
"""Refresh openly licensed third-party compute-universe snapshots.

Each source is stored separately and byte-for-byte as published. Nothing is
inferred and the source populations are never summed into a global census.

A source is skipped (not failed) when its robots.txt disallows automated
access; a failed download keeps the previously retained snapshot. The status
file records what happened to every source on every run.

    python scripts/sync_global_compute_sources.py            # refresh
    python scripts/sync_global_compute_sources.py --selftest # offline parser checks

Exit status is 1 only when a source failed for a reason other than policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from polite_fetch import RobotsDisallowed, fetch_bytes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data/global_compute_universe_snapshot_status.json"

SOURCES = [
    {
        "name": "Compute Atlas",
        "url": "https://www.compute-atlas.com/api/facilities",
        "info_url": "https://www.compute-atlas.com/data",
        "path": ROOT / "data/external/compute_atlas/facilities.json",
        "license": "CC BY 4.0",
    },
    {
        "name": "Data Center Index",
        "url": "https://datacenterindex.ai/data/datacenterindex-campuses.json",
        "info_url": "https://datacenterindex.ai/data",
        "path": ROOT / "data/external/data_center_index/campuses.json",
        "license": "CC BY 4.0",
    },
]

# Publishers have used several envelope shapes for the same list over time.
RECORD_KEYS = ("facilities", "rows", "items", "records", "data", "campuses")


def records_of(payload) -> list:
    """Return the record list from a publisher payload, or raise ValueError."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in RECORD_KEYS:
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError("unexpected JSON shape: expected a list or an object holding one of " + ", ".join(RECORD_KEYS))


def refresh_one(src: dict, retrieved_at: str) -> dict:
    entry = {"name": src["name"], "url": src["url"], "info_url": src["info_url"], "license": src["license"],
             "local_snapshot": str(src["path"].relative_to(ROOT)).replace("\\", "/"), "checked_at": retrieved_at}
    try:
        body = fetch_bytes(src["url"])
        records = records_of(json.loads(body.decode("utf-8")))
        if not records:
            raise ValueError("publisher returned zero records")
    except RobotsDisallowed as exc:
        return {**entry, "status": "SKIPPED_ROBOTS_DISALLOWED", "detail": str(exc),
                "snapshot_present": src["path"].exists()}
    except Exception as exc:  # noqa: BLE001 - recorded, previous snapshot kept
        return {**entry, "status": "FAILED", "detail": f"{type(exc).__name__}: {exc}"[:500],
                "snapshot_present": src["path"].exists()}
    src["path"].parent.mkdir(parents=True, exist_ok=True)
    if not src["path"].exists() or src["path"].read_bytes() != body:
        tmp = src["path"].with_suffix(src["path"].suffix + ".tmp")
        tmp.write_bytes(body)
        tmp.replace(src["path"])
    return {**entry, "status": "OK", "snapshot_present": True, "record_count": len(records),
            "retrieved_at": retrieved_at, "sha256": hashlib.sha256(body).hexdigest()}


def selftest() -> None:
    assert records_of([{"a": 1}]) == [{"a": 1}]
    assert records_of({"facilities": [1, 2]}) == [1, 2]
    assert records_of({"license": "x", "count": 2, "rows": [1, 2]}) == [1, 2]
    try:
        records_of({"count": 3})
    except ValueError:
        pass
    else:
        raise AssertionError("an object without a record list must be rejected")
    print("PASS: global compute source parser self-test (4 checks)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        selftest()
        return 0
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    sources = [refresh_one(src, retrieved_at) for src in SOURCES]
    status = {"schema_version": 2, "generated_on": str(date.today()), "sources": sources,
              "policy": ("Third-party snapshots are fetched only where the publisher's robots.txt allows "
                         "automated access; otherwise the page links to the publisher's own data page.")}
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 1 if any(s["status"] == "FAILED" for s in sources) else 0


if __name__ == "__main__":
    sys.exit(main())
