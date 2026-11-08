"""Track 3 ledgers, the static API, and the facility-record shards (offline)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def reference_sites() -> int:
    return len(load("data/external/epoch_ai/site_level_connection_evidence.json")["records"])


def test_track3_ledgers_join():
    for rel in ("data/track3_evidence_schema.json", "data/track3_source_stack.json", "data/track3/site_status.json",
                "data/track3/evidence_records.json", "data/track3/research_queue.json", "data/track3/summary.json"):
        load(rel)
    n = reference_sites()
    summary = load("data/track3/summary.json")
    queue = load("data/track3/research_queue.json")
    epoch = load("data/external/epoch_ai/site_level_connection_evidence.json")
    evidence = load("data/track3/evidence_records.json")
    assert summary["epoch_site_count"] == len(load("data/track3/site_status.json")["records"]) == n
    assert evidence["record_count"] == len(evidence["records"])
    assert queue["count"] == len(queue["records"]) == summary["pending_grid_connection_research_count"]
    assert epoch["record_count"] == epoch["summary"]["total"] == n
    assert epoch["summary"]["evidence_found"] == summary["site_level_evidence_site_count"]


def test_static_api_contracts():
    for rel in ("api/v1/facilities.json", "api/v1/openapi.json", "data/bulk_download_manifest.json", "data/epoch_ai_map.json"):
        load(rel)
    with (ROOT / "data/external/epoch_ai/crosswalk.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows and all(r.get("epoch_id") for r in rows) and len({r["epoch_id"] for r in rows}) == len(rows)
    api = load("api/v1/facilities.json")
    assert api["record_count"] == len(api["records"]) == len({x["facility_id"] for x in api["records"]}) == reference_sites()
    openapi = load("api/v1/openapi.json")
    assert "/api/v1/facilities.json" in openapi["paths"]
    assert "/data/facility_records/{rto}/{shard}.json" in openapi["paths"]


def test_track3_runtime_contracts():
    summary = load("data/track3/summary.json")
    evidence = load("data/track3/evidence_records.json")
    audit = load("data/website_completeness_audit.json")["summary"]
    transformer = load("data/track3/transformer_supply_chain_events.json")
    assert len(load("data/track3/observation_queue.json")["tasks"]) == summary["observation_task_count"]
    assert audit["track3_evidence_records"] == evidence["record_count"] == len(evidence["records"])
    assert load("data/physical_verification_layer.json")["summary"]["transformer_event_records"] \
        == transformer["record_count"] == len(transformer["records"])


def test_public_interface_markers():
    for page in ("facility.html", "api.html", "bulk-download.html"):
        assert (ROOT / page).stat().st_size > 0, page
    facility = (ROOT / "facility.html").read_text(encoding="utf-8")
    track3 = (ROOT / "track3.html").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "facility.html?facility=" in track3
    assert "Download facility record JSON" in facility and "Download facility CSV" in facility
    assert "source document" in facility.lower()
    assert "Mexican state boundaries" in index and "Mexican state boundaries" in track3


def test_facility_record_shards():
    idx = load("data/facility_records/index.json")
    expected = load("data/large_load_scope.json")["definitions"]["current_row_level"]["records"]
    assert idx["record_count"] == sum(idx["rto_counts"].values()) == expected
    total = 0
    for rto, rel in idx["files"].items():
        shard_index = load(rel)
        assert shard_index["rto"] == rto
        assert shard_index["record_count"] == sum(s["record_count"] for s in shard_index["shards"]) == idx["rto_counts"][rto]
        for shard in shard_index["shards"]:
            assert (ROOT / shard["file"]).exists(), shard["file"]
        total += shard_index["record_count"]
    assert total == expected
