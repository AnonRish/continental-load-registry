#!/usr/bin/env python3
"""Refresh retained Track 3 physical-artifact provenance manifest."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from build_physical_provenance_manifest import ARTIFACT_ROLES, retained_entry

ROOT=Path(__file__).resolve().parents[1]
TRACK3=ROOT/"data"/"track3"
OUT=TRACK3/"physical_source_manifest.json"
REQUIRED=[
 ("data/track3/remote_sensing_observations.json","Canonical derived scene ledger"),
 ("data/track3/remote_sensing_observations.csv","Flattened derived scene ledger"),
 ("data/track3/building_footprints_index.json","93-site footprint acquisition/index manifest"),
 ("data/physical_verification_layer.json","Aggregate physical-verification state layer"),
 ("data/track3/physical_site_coordinates.json","Geocoding/coordinate provenance cache"),
]
def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))
def main()->int:
    existing=load(OUT) if OUT.exists() else {}
    physical=load(ROOT/"data/physical_verification_layer.json")
    obs=load(TRACK3/"remote_sensing_observations.json")
    foot=load(TRACK3/"building_footprints_index.json")
    coords=load(TRACK3/"physical_site_coordinates.json")
    derived_rows=[x for x in obs.get("records",[]) if x.get("status")=="INGESTED_DERIVED"]
    derived_count=len(derived_rows)
    derived_sites=len({str(x.get("epoch_id")) for x in derived_rows if x.get("epoch_id")})
    modality_counts={
        modality:sum(1 for x in derived_rows if str(x.get("modality") or "").lower()==modality)
        for modality in ("optical","tir","sar")
    }
    # Keep the aggregate physical verification layer synchronized with its canonical
    # scene ledger before hashing/publishing the retained artifacts.
    today=datetime.now(timezone.utc).date().isoformat()
    physical_summary=physical.setdefault("summary", {})
    reconciled={
        "raw_optical_scenes_ingested":modality_counts["optical"],
        "raw_tir_numeric_observations":modality_counts["tir"],
        "raw_sar_numeric_observations":modality_counts["sar"],
        "derived_observation_count":derived_count,
        "derived_observation_sites":derived_sites,
        "derived_observations":derived_count,
        "derived_observation_ledger":"data/track3/remote_sensing_observations.json",
    }
    if any(physical_summary.get(k)!=v for k,v in reconciled.items()) or "reconciled_on" not in physical_summary:
        physical_summary.update(reconciled)
        physical_summary["reconciled_on"]=today  # only when the reconciled counts actually changed
        (ROOT/"data/physical_verification_layer.json").write_text(
            json.dumps(physical,indent=2,ensure_ascii=False)+"\n",
            encoding="utf-8",
        )
    for rel,_role in REQUIRED:
        path=ROOT/rel
        if not path.exists() or path.stat().st_size==0: raise SystemExit(f"FAIL: missing retained physical artifact: {rel}")
    # Hash after the physical layer is written, with the same function --check uses.
    retained=[retained_entry(rel) for rel in ARTIFACT_ROLES]
    polygon_sites=int(foot.get("sites_with_polygon_files") or 0)
    target_count=len(coords.get("records",[])); geocoded=sum(1 for x in coords.get("records",[]) if x.get("lat") is not None and x.get("lon") is not None)
    manifest={
     "schema_version":2,
     "title":existing.get("title") or "Track 3 physical-source and retained-artifact provenance manifest",
     "generated_on":datetime.now(timezone.utc).date().isoformat(),
     "scope":existing.get("scope") or "Public physical-evidence acquisition for the 93-site Epoch AI reference universe",
     "hash_policy":{**(existing.get("hash_policy") or {}),"retained_artifact_integrity":"Repository-retained artifact bytes are SHA-256 hashed and byte-counted on every refresh.","scene_level_reproducibility":"Every derived remote-sensing record retains the STAC item URL, scene ID, observation date, source collection, and processing version."},
     "sources":existing.get("sources") or [],"retained_artifacts":retained,
     "acquisition_outputs":{"epoch_site_target_count":target_count,"epoch_site_geocoded_count":geocoded,"epoch_site_unresolved_coordinate_count":target_count-geocoded,"remote_sensing_derived_observation_count":derived_count,"building_footprint_polygon_site_count":polygon_sites,"building_footprint_geojson_file_count":polygon_sites},
     "semantics":existing.get("semantics") or "A source scene, building footprint, thermal anomaly, SAR metric, NDVI metric, or geocoded coordinate is an observation layer, not by itself proof of AI compute, ownership, tenancy, or covert activity. Missing source bytes or missing observations are not evidence of absence.",
     "last_reconciled_on":existing.get("last_reconciled_on") or today,
    }
    content_keys=("retained_artifacts","acquisition_outputs")
    if any(existing.get(k)!=manifest[k] for k in content_keys):
        manifest["generated_on"]=today
        manifest["last_reconciled_on"]=today
    else:
        manifest["generated_on"]=existing.get("generated_on") or today
    OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(manifest["acquisition_outputs"],indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
