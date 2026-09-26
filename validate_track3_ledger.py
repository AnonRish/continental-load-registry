#!/usr/bin/env python3
"""Validate the canonical Track 3 artifacts and their source-layer joins."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACK3 = ROOT / "data" / "track3"
EPOCH = ROOT / "data" / "external" / "epoch_ai"
ALLOWED = {"VERIFIED_SITE_SPECIFIC", "SITE_LEVEL_EVIDENCE", "PENDING_RESEARCH"}

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def crosswalk_is_connection(item: dict | None) -> bool:
    text = str((item or {}).get("status") or "").lower()
    return any(x in text for x in ("grid_record", "utility_record", "service_record", "regulatory_record", "power_request", "load_request"))

def main() -> int:
    summary = load(TRACK3 / "summary.json")
    site_status = load(TRACK3 / "site_status.json")
    evidence = load(TRACK3 / "evidence_records.json")
    queue = load(TRACK3 / "research_queue.json")
    registry = load(EPOCH / "registry.json")
    source_evidence = load(EPOCH / "site_level_connection_evidence.json")
    crosswalk = load(EPOCH / "queue_crosswalk.json")
    source_stack = load(ROOT / "data" / "track3_source_stack.json")
    sites = site_status.get("records", [])
    ids = [x.get("epoch_id") for x in sites]
    if len(sites) != 93 or len(set(ids)) != 93 or any(not x for x in ids):
        raise SystemExit("FAIL: Track 3 site_status must contain 93 unique Epoch IDs")
    for payload, name in ((registry, "registry"), (source_evidence, "site evidence"), (crosswalk, "crosswalk")):
        if len(payload.get("records", [])) != 93:
            raise SystemExit(f"FAIL: {name} must contain 93 records")
    expected_ids = set(ids)
    if expected_ids != {x.get("epoch_id") for x in registry["records"]}:
        raise SystemExit("FAIL: site_status and Epoch registry IDs differ")
    if expected_ids != {x.get("epoch_id") for x in source_evidence["records"]}:
        raise SystemExit("FAIL: site_status and site-evidence IDs differ")
    if expected_ids != {x.get("epoch_id") for x in crosswalk["records"]}:
        raise SystemExit("FAIL: site_status and crosswalk IDs differ")
    grid_counts = {k: sum(1 for x in sites if x.get("domains", {}).get("grid_connection", {}).get("status") == k) for k in ALLOWED}
    if sum(grid_counts.values()) != 93:
        raise SystemExit(f"FAIL: grid-connection status counts do not sum to 93: {grid_counts}")
    if summary.get("domain_status_counts", {}).get("grid_connection") != grid_counts:
        raise SystemExit("FAIL: summary grid-connection counts do not match site_status")
    combined = sum(1 for x in sites if int(x.get("combined_site_level_evidence_count", 0)) > 0)
    if summary.get("combined_site_level_evidence_site_count") != combined:
        raise SystemExit("FAIL: combined site-evidence count does not match site_status")
    pending = [x for x in sites if x.get("domains", {}).get("grid_connection", {}).get("status") == "PENDING_RESEARCH"]
    if queue.get("count") != len(pending) or len(queue.get("records", [])) != len(pending):
        raise SystemExit("FAIL: research queue does not match pending grid research")
    cross_count = sum(1 for x in crosswalk["records"] if x.get("site_level_public_evidence"))
    base_evidence_items = sum(len(x.get("site_level_evidence") or []) for x in source_evidence["records"])
    expected_evidence_items = base_evidence_items + cross_count
    if evidence.get("record_count") != expected_evidence_items or len(evidence.get("records", [])) != expected_evidence_items:
        raise SystemExit(f"FAIL: evidence record count mismatch: expected {expected_evidence_items}, got {evidence.get("record_count")}")
    if summary.get("source_stack_count") != len(source_stack.get("sources", [])):
        raise SystemExit("FAIL: summary source_stack_count does not match catalog")
    for rec in sites:
        grid_state = (next((x.get("state_province") for x in crosswalk["records"] if x.get("epoch_id") == rec.get("epoch_id")), "") or "").strip()
        if grid_state and rec.get("state_province") != grid_state:
            raise SystemExit(f"FAIL: {rec.get("epoch_id")} state_province does not match curated crosswalk state")

    for rec in sites:
        state = rec.get("domains", {}).get("grid_connection", {}).get("status")
        if state not in ALLOWED:
            raise SystemExit(f"FAIL: invalid grid_connection state on {rec.get("epoch_id")}: {state}")
        if rec.get("grid", {}).get("site_specific_queue_id") and state != "VERIFIED_SITE_SPECIFIC":
            raise SystemExit(f"FAIL: queue ID present without VERIFIED_SITE_SPECIFIC on {rec.get("epoch_id")}")
    print("PASS: canonical Track 3 integrity checks passed")
    print(f"93 Epoch IDs aligned; grid states={grid_counts}; combined site evidence={combined}; evidence items={expected_evidence_items}; pending grid research={len(pending)}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
