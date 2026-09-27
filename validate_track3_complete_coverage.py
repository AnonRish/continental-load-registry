#!/usr/bin/env python3
"""Validate the complete Track 3 repository coverage contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED_ARTIFACTS = [
    "data/track3/track3_completeness_matrix.json",
    "data/track3/global_compute_supply_chain.json",
    "data/track3/public_global_source_observations.json",
    "data/track3/certificate_model.json",
    "data/track3/audit_population_protocol.json",
    "data/track3/sampling_protocol.json",
    "data/track3/inspection_protocol.json",
    "data/track3/serial_continuity_protocol.json",
    "data/track3/decommissioning_protocol.json",
    "data/track3/untraced_compute_pool.json",
    "data/track3/disclosure_protocol.json",
    "data/track3/remote_sensing_observation_targets.json",
    "data/track3/remote_sensing_observations.json",
    "data/track3/observation_queue.json",
    "data/track3/site_status.json",
    "TRACK3_COMPLETE_COVERAGE.md",
    "CLOSED_CASE_PROTOCOL.md",
    "track3_certificate.py",
]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_ARTIFACTS:
        path = ROOT / rel
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing or empty artifact: {rel}")

    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        return 1

    matrix = load("data/track3/track3_completeness_matrix.json")
    rows = matrix.get("rows", [])
    if len(rows) < 17:
        errors.append(f"expected at least 17 Track 3 matrix rows, got {len(rows)}")

    for row in rows:
        for key in ("id", "requirement", "implementation", "status", "evidence", "blocking_gap"):
            if not row.get(key):
                errors.append(f"{row.get('id', 'UNKNOWN')}: missing matrix field {key}")

    phys = load("data/track3/remote_sensing_observations.json")
    if phys.get("observation_count", 0) < phys.get("derived_observation_count", 0):
        errors.append("remote-sensing derived count exceeds observation count")

    targets = load("data/track3/remote_sensing_observation_targets.json")
    if targets.get("record_count") != 93 or len(targets.get("records", [])) != 93:
        errors.append("remote-sensing target universe is not exactly 93 records")
    if targets.get("summary", {}).get("derived_observation_count") != phys.get("derived_observation_count"):
        errors.append("remote-sensing target summary does not reconcile with observation ledger")

    sites = load("data/track3/site_status.json")
    if sites.get("summary", {}).get("epoch_site_count") != 93:
        errors.append("site-status epoch universe is not 93")

    accounting = load("data/track3/global_compute_supply_chain.json")
    if accounting.get("current", {}).get("global_transaction_level_closure") != "UNKNOWN":
        errors.append("global transaction-level closure must remain explicitly UNKNOWN")

    residual = load("data/track3/untraced_compute_pool.json")
    if residual.get("current_snapshot", {}).get("status") != "UNKNOWN":
        errors.append("untraced pool must remain UNKNOWN until transaction inputs close")

    inspection = load("data/track3/inspection_protocol.json")
    if inspection.get("current_observation_count") != 0:
        errors.append("inspection count changed without an independently retained inspection ledger")

    certificate = load("data/track3/certificate_model.json")
    if certificate.get("status") != "FRAMEWORK_IMPLEMENTED":
        errors.append("certificate model status changed unexpectedly")

    global_sources = load("data/track3/public_global_source_observations.json")
    if len(global_sources.get("observations", [])) < 6:
        errors.append("global public source observation inventory is incomplete")

    if errors:
        print("\n".join("ERROR: " + e for e in errors))
        return 1

    print(f"PASS: complete Track 3 coverage contract validated ({len(rows)} matrix rows, 93-site reference universe)")
    print("PASS: explicit UNKNOWN states retained where public/authorized evidence is not available")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
