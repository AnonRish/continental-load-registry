#!/usr/bin/env python3
"""Validate Track 3 physical-source provenance contracts without network access."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data" / "track3" / "physical_source_manifest.json"
OBS = ROOT / "data" / "track3" / "remote_sensing_observations.json"
FOOT = ROOT / "data" / "track3" / "building_footprints_index.json"
PHYSICAL = ROOT / "data" / "physical_verification_layer.json"

REQUIRED_SOURCE_IDS = {
    "sentinel-2-optical",
    "sentinel-1-sar",
    "landsat-c2-l2-st",
    "overture-buildings",
}

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    manifest = load(MANIFEST)
    obs = load(OBS)
    foot = load(FOOT)
    physical = load(PHYSICAL)

    sources = {str(x.get("id")): x for x in manifest.get("sources", [])}
    missing = REQUIRED_SOURCE_IDS - set(sources)
    if missing:
        raise SystemExit(f"FAIL: physical manifest missing sources: {sorted(missing)}")

    if manifest.get("acquisition_outputs", {}).get("epoch_site_target_count") != 93:
        raise SystemExit("FAIL: physical manifest target count is not 93")

    if obs.get("site_count_target") != 93:
        raise SystemExit("FAIL: remote-sensing site target count is not 93")
    records = obs.get("records", [])
    derived = [row for row in records if row.get("status") == "INGESTED_DERIVED"]
    if obs.get("derived_observation_count") != len(derived):
        raise SystemExit("FAIL: remote-sensing derived count does not match records")

    for row in derived:
        for key in ("epoch_id", "scene_id", "observed_on", "stac_item_url", "source_catalog", "source_collection"):
            if not row.get(key):
                raise SystemExit(f"FAIL: derived scene record missing {key}: {row.get('scene_id')!r}")

    if foot.get("site_target_count") != 93:
        raise SystemExit("FAIL: building-footprint target count is not 93")
    polygonized = [row for row in foot.get("records", []) if row.get("status") == "INGESTED_POLYGONIZED"]
    if len(polygonized) != foot.get("sites_with_polygon_files"):
        raise SystemExit("FAIL: polygon site count does not match footprint records")
    for row in polygonized:
        if not row.get("geometry_file"):
            raise SystemExit(f"FAIL: polygonized site has no geometry file: {row.get('epoch_id')}")
        if not row.get("source_release"):
            raise SystemExit(f"FAIL: polygonized site has no source release: {row.get('epoch_id')}")

    retained = {str(x.get("path")): x for x in manifest.get("retained_artifacts", [])}
    required = {
        "data/track3/remote_sensing_observations.json",
        "data/track3/remote_sensing_observations.csv",
        "data/track3/building_footprints_index.json",
        "data/physical_verification_layer.json",
        "data/track3/physical_site_coordinates.json",
    }
    missing_artifacts = required - set(retained)
    if missing_artifacts:
        raise SystemExit(f"FAIL: manifest missing retained artifacts: {sorted(missing_artifacts)}")

    import hashlib
    for rel, entry in retained.items():
        path = ROOT / rel
        if not path.exists() or path.stat().st_size == 0:
            raise SystemExit(f"FAIL: retained manifest artifact missing/empty: {rel}")
        if entry.get("bytes") is not None and int(entry["bytes"]) != path.stat().st_size:
            raise SystemExit(f"FAIL: retained artifact byte count disagrees: {rel}")
        if entry.get("sha256"):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != entry["sha256"]:
                raise SystemExit(f"FAIL: retained artifact SHA-256 disagrees: {rel}")

    outputs = manifest.get("acquisition_outputs", {})
    if outputs.get("remote_sensing_derived_observation_count") != len(derived):
        raise SystemExit("FAIL: manifest remote-sensing count disagrees with observations")
    if outputs.get("building_footprint_polygon_site_count") != foot.get("sites_with_polygon_files"):
        raise SystemExit("FAIL: manifest footprint site count disagrees with footprint index")

    if not isinstance(physical, dict):
        raise SystemExit("FAIL: physical verification layer is not an object")

    for source in sources.values():
        if not source.get("raw_source_retained") and source.get("raw_source_sha256") is not None:
            raise SystemExit(f"FAIL: raw SHA-256 supplied for non-retained source: {source.get('id')}")

    print(
        "PASS: physical provenance contracts passed "
        f"(93 site targets; {len(derived)} derived records; "
        f"{foot.get('sites_with_polygon_files')} polygonized sites)."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
