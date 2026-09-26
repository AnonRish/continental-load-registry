#!/usr/bin/env python3
"""Validate the unified Track 3 evidence ledger."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "data" / "track3_evidence_ledger.json"
REGISTRY = ROOT / "data" / "external" / "epoch_ai" / "registry.json"
CROSSWALK = ROOT / "data" / "external" / "epoch_ai" / "queue_crosswalk.json"
EVIDENCE = ROOT / "data" / "external" / "epoch_ai" / "site_level_connection_evidence.json"
ALLOWED_STATES = {"SITE_QUEUE_ID_VERIFIED","SITE_LEVEL_EVIDENCE_FOUND","JURISDICTION_ONLY","EXTERNAL_CONNECTION_SYSTEM_MAPPED"}
def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
def main() -> int:
    ledger, registry, crosswalk, evidence = map(load, [LEDGER, REGISTRY, CROSSWALK, EVIDENCE])
    records = ledger.get("records", [])
    if ledger.get("schema_version") != 1 or ledger.get("as_of") != "2026-09-26":
        raise SystemExit("FAIL: unsupported Track 3 ledger metadata")
    if len(records) != 93 or ledger.get("counts", {}).get("sites") != 93:
        raise SystemExit("FAIL: ledger must contain exactly 93 records")
    ids = [r.get("epoch_id") for r in records]
    if len(set(ids)) != 93 or any(not x for x in ids):
        raise SystemExit("FAIL: duplicate or blank Epoch IDs")
    expected = {r.get("epoch_id") for r in registry.get("records", [])}
    if set(ids) != expected:
        raise SystemExit("FAIL: ledger IDs do not match Epoch registry")
    if set(ids) != {r.get("epoch_id") for r in crosswalk.get("records", [])}:
        raise SystemExit("FAIL: ledger IDs do not match queue crosswalk")
    if set(ids) != {r.get("epoch_id") for r in evidence.get("records", [])}:
        raise SystemExit("FAIL: ledger IDs do not match site-evidence layer")
    required_domains = {"electricity_connection","physical_site","actual_electricity_metering","tir_thermal","sar_optical_change_detection","transformer_supply_chain","chip_inventory","ownership_accounting","independent_corroboration"}
    for r in records:
        state = r.get("verification_state")
        if state not in ALLOWED_STATES:
            raise SystemExit(f"FAIL: {r.get("epoch_id")} has invalid verification_state={state!r}")
        grid = r.get("grid") or {}
        attached = (r.get("evidence") or {}).get("attached") or []
        if grid.get("site_specific_queue_id") and state != "SITE_QUEUE_ID_VERIFIED":
            raise SystemExit(f"FAIL: {r.get("epoch_id")} has a queue ID but wrong state")
        if state == "SITE_LEVEL_EVIDENCE_FOUND" and not attached:
            raise SystemExit(f"FAIL: {r.get("epoch_id")} claims evidence without attached record")
        if set((r.get("domains") or {}).keys()) != required_domains:
            raise SystemExit(f"FAIL: {r.get("epoch_id")} has an incomplete domain map")
    counts = ledger["counts"]
    checks = {
        "site_queue_id_verified": sum(r["verification_state"] == "SITE_QUEUE_ID_VERIFIED" for r in records),
        "site_level_evidence_found": sum(r["verification_state"] in {"SITE_QUEUE_ID_VERIFIED","SITE_LEVEL_EVIDENCE_FOUND"} for r in records),
        "jurisdiction_only": sum(r["verification_state"] == "JURISDICTION_ONLY" for r in records),
        "external_connection_system_mapped": sum(r["verification_state"] == "EXTERNAL_CONNECTION_SYSTEM_MAPPED" for r in records),
        "timeline_sites": sum(bool(r.get("timeline")) for r in records),
        "chip_quantity_sites": sum(bool(r.get("chip_quantities")) for r in records),
    }
    for k, v in checks.items():
        if counts.get(k) != v:
            raise SystemExit(f"FAIL: count mismatch for {k}: ledger={counts.get(k)} derived={v}")
    print("PASS: Track 3 ledger integrity checks passed")
    print(checks)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())