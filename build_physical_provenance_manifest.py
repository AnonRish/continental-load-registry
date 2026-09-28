#!/usr/bin/env python3
"""Rebuild the retained-artifact section of the Track 3 provenance manifest.

The command is deterministic for repository-retained bytes. It does not download
or hash unretained satellite rasters, and it never treats missing raw bytes as
evidence of absence.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MANIFEST=ROOT/"data/track3/physical_source_manifest.json"

ARTIFACT_META={
 "data/track3/remote_sensing_observations.json": ("Canonical derived scene ledger","record_count","derived_observation_count"),
 "data/track3/remote_sensing_observations.csv": ("Flattened derived scene ledger",None,None),
 "data/track3/building_footprints_index.json": ("93-site footprint acquisition/index manifest","record_count","sites_with_polygon_files"),
 "data/physical_verification_layer.json": ("Aggregate physical-verification state layer",None,None),
 "data/track3/physical_site_coordinates.json": ("Geocoding/coordinate provenance cache","record_count",None),
}

def digest(path:Path)->tuple[str,int]:
 h=hashlib.sha256()
 n=0
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):
   n+=len(chunk); h.update(chunk)
 return h.hexdigest(),n

def replacement_manifest()->dict:
 obj=json.loads(MANIFEST.read_text(encoding="utf-8"))
 retained=[]
 for rel,(role,count_key,extra_key) in ARTIFACT_META.items():
  path=ROOT/rel
  if not path.exists() or path.stat().st_size==0:
   raise SystemExit(f"missing/empty retained artifact: {rel}")
  sha,n=digest(path)
  entry={"path":rel,"role":role,"sha256":sha,"bytes":n}
  if count_key:
   data=json.loads(path.read_text(encoding="utf-8"))
   entry["record_count"]=len(data.get("records",[])) if count_key=="record_count" else data.get(count_key)
   if extra_key:
    entry["polygon_site_count"]=data.get(extra_key)
  elif rel.endswith("remote_sensing_observations.csv"):
   # CSV is a flattened export; derive its row count without altering it.
   with path.open("r",encoding="utf-8",newline="") as f:
    entry["row_count"]=max(0,sum(1 for _ in f)-1)
  elif rel.endswith("physical_verification_layer.json"):
   data=json.loads(path.read_text(encoding="utf-8"))
   entry["site_record_count"]=len(data.get("sites",data.get("records",[])))
  retained.append(entry)
 obj["retained_artifacts"]=retained
 obs=json.loads((ROOT/"data/track3/remote_sensing_observations.json").read_text(encoding="utf-8"))
 foot=json.loads((ROOT/"data/track3/building_footprints_index.json").read_text(encoding="utf-8"))
 coord=json.loads((ROOT/"data/track3/physical_site_coordinates.json").read_text(encoding="utf-8"))
 obj.setdefault("acquisition_outputs",{})["remote_sensing_derived_observation_count"]=int(obs.get("derived_observation_count",0))
 obj["acquisition_outputs"]["building_footprint_polygon_site_count"]=int(foot.get("sites_with_polygon_files",0))
 obj["acquisition_outputs"]["epoch_site_geocoded_count"]=sum(1 for x in coord.get("records",[]) if x.get("lat") is not None and x.get("lon") is not None)
 obj["acquisition_outputs"]["epoch_site_unresolved_coordinate_count"]=int(obj["acquisition_outputs"]["epoch_site_target_count"])-obj["acquisition_outputs"]["epoch_site_geocoded_count"]
 obj["last_reconciled_on"]=__import__("datetime").date.today().isoformat()
 return obj

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--check",action="store_true")
 args=ap.parse_args()
 current=json.loads(MANIFEST.read_text(encoding="utf-8"))
 rebuilt=replacement_manifest()
 same=json.dumps(current,indent=2,ensure_ascii=False)+"
" == json.dumps(rebuilt,indent=2,ensure_ascii=False)+"
"
 if args.check:
  print("PASS: physical provenance manifest is reproducible." if same else "FAIL: physical provenance manifest is stale.")
  return 0 if same else 1
 MANIFEST.write_text(json.dumps(rebuilt,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
 print("WROTE:",MANIFEST)
 return 0
if __name__=="__main__": raise SystemExit(main())
