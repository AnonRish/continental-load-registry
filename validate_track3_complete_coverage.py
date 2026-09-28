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
    "data/track3/public_web_claims.json",
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
    "data/track3/geo_coverage_audit_2026-09-27.json",
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

    geo = load("data/track3/geo_coverage_audit_2026-09-27.json")
    if geo.get("scope", {}).get("epoch_reference_sites") != 93:
        errors.append("physical-coordinate audit scope is not 93")
    if len(geo.get("records", [])) != 93:
        errors.append("physical-coordinate audit is not exactly 93 records")
    if geo.get("summary", {}).get("resolved_sites", -1) + geo.get("summary", {}).get("unresolved_sites", -1) != 93:
        errors.append("physical-coordinate audit resolved/unresolved counts do not reconcile")

    targets = load("data/track3/remote_sensing_observation_targets.json")
    if targets.get("record_count") != 93 or len(targets.get("records", [])) != 93:
        errors.append("remote-sensing target universe is not exactly 93 records")
    if targets.get("summary", {}).get("derived_observation_count") != phys.get("derived_observation_count"):
        errors.append("remote-sensing target summary does not reconcile with observation ledger")

    sites = load("data/track3/site_status.json")
    if sites.get("summary", {}).get("epoch_site_count") != 93:
        errors.append("site-status epoch universe is not 93")

    coord_status = {str(x.get("epoch_id")): x.get("coordinate_status") for x in geo.get("records", [])}
    for x in geo.get("records", []):
        if x.get("coordinate_status") == "RESOLVED":
            if x.get("latitude") is None or x.get("longitude") is None:
                errors.append(f"{x.get('epoch_id')}: RESOLVED coordinate lacks lat/lon")
        elif x.get("coordinate_status") == "UNRESOLVED":
            if x.get("latitude") is not None or x.get("longitude") is not None:
                errors.append(f"{x.get('epoch_id')}: UNRESOLVED coordinate contains lat/lon")

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

    public_claims = load("data/track3/public_web_claims.json")
    enrichment = load("data/track3/public_web_enrichment_2026-09-27.json")
    claim_rows = public_claims.get("claims", [])
    enrichment_rows = enrichment.get("records", [])
    if public_claims.get("accounting", {}).get("claim_count") != len(claim_rows):
        errors.append("public-web claim count does not reconcile")
    if len(claim_rows) != len(enrichment_rows):
        errors.append("public-web claim layer is not 1:1 with enrichment records")
    claim_ids = [str(x.get("claim_id")) for x in claim_rows]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("public-web claim IDs are not unique")

    def source_key(x):
        payload = {
            "site_name": x.get("site_name"),
            "field": x.get("field"),
            "value": x.get("value"),
            "relationship": x.get("relationship"),
            "source": x.get("source"),
            "source_urls": x.get("source_urls") or [],
            "publication_date": x.get("publication_date"),
        }
        import hashlib
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

    enrichment_keys = [source_key(x) for x in enrichment_rows]
    claim_keys = [source_key(x) for x in claim_rows]
    if len(enrichment_keys) != len(set(enrichment_keys)):
        errors.append("public-web enrichment source keys are not unique")
    if len(claim_keys) != len(set(claim_keys)):
        errors.append("public-web claim source keys are not unique")
    if set(enrichment_keys) != set(claim_keys):
        errors.append("public-web claims do not reconcile 1:1 with enrichment records")

    for x in claim_rows:
        if not x.get("claim_id") or not x.get("field"):
            errors.append("public-web claim missing claim_id or field")
        if x.get("claim_scope") == "site_level_public_web" and not x.get("epoch_id"):
            errors.append(f"site-scoped public-web claim {x.get('claim_id')} missing epoch_id")
        if not (x.get("source_urls") or []):
            errors.append(f"public-web claim {x.get('claim_id')} has no retained source URL")
    if public_claims.get("accounting", {}).get("claim_count", 0) < 335:
        errors.append("public-web claim layer is missing retained enrichment claims")

    leads = load("data/track3/public_research_leads.json")
    lead_rows = leads.get("records", [])
    assert leads.get("accounting", {}).get("lead_count") == len(lead_rows) == 53
    assert leads.get("accounting", {}).get("site_count") == 33
    assert len({x.get("lead_id") for x in lead_rows}) == len(lead_rows)
    assert all(x.get("epoch_id") and x.get("field") and x.get("finding") for x in lead_rows)
    assert all(x.get("status") in {"PUBLIC_LEAD_REVIEW_REQUIRED","RETAINED_SOURCE","PUBLIC_SOURCE"} for x in lead_rows)

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
