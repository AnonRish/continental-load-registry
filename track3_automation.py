#!/usr/bin/env python3
"""Unified Track 3 automation/control-plane checks.

This script intentionally separates:
- automated ingestion adapters;
- source health/change monitoring;
- queue release diffing;
- duplicate/geographic checks;
- evidence/entity validation;
- consolidated data-quality reporting.

A source without a repository adapter is never labeled as ingested.
"""
from __future__ import annotations
import csv,hashlib,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"
AUTO=DATA/"automation"
NOW=datetime.now(timezone.utc)
NOW_ISO=NOW.isoformat()
TODAY=NOW.date().isoformat()

AUTOMATED_ADAPTERS={
 "PJM":(".github/workflows/sync_pjm_cycle_public_queue.yml","sync_pjm_cycle_public_queue.py"),
 "MISO":(".github/workflows/sync_miso_public_queue.yml","sync_miso_public_queue.py"),
 "CAISO":(".github/workflows/sync_caiso_public_queue.yml","sync_caiso_public_queue.py"),
 "NYISO":(".github/workflows/sync_nyiso_public_queue.yml","sync_nyiso_public_queue.py"),
 "SPP":(".github/workflows/sync_spp_public_queue.yml","sync_spp_public_queue.py"),
 "ERCOT":(".github/workflows/track3_automated_pipeline.yml","sync_auxiliary_queue_sources.py"),
 "ISO-NE":(".github/workflows/track3_automated_pipeline.yml","sync_auxiliary_queue_sources.py"),
 "IESO":(".github/workflows/track3_automated_pipeline.yml","sync_auxiliary_queue_sources.py"),
 "AESO":(".github/workflows/track3_automated_pipeline.yml","sync_auxiliary_queue_sources.py"),
 "epoch-data-centers":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_epoch_ai_data_centers.py"),
 "epoch-chip-sales":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_track3_external_sources.py"),
 "epoch-chip-owners":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_track3_external_sources.py"),
 "epoch-chip-users":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_track3_external_sources.py"),
 "epoch-gpu-clusters":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_track3_external_sources.py"),
 "epoch-chip-components":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_track3_external_sources.py"),
 "epoch-timelines":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_epoch_ai_data_centers.py"),
 "epoch-chip-quantities":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_epoch_ai_data_centers.py"),
 "epoch-chillers":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_epoch_ai_data_centers.py"),
 "epoch-cooling-towers":(".github/workflows/sync_epoch_ai_data_centers.yml","sync_epoch_ai_data_centers.py"),
 "physical-verification-layer":(".github/workflows/physical_verification.yml","module1_physical_radar.py"),
 "overture-buildings":(".github/workflows/track3_building_footprints.yml","build_building_footprints.py"),
}
MANUAL_SNAPSHOT={"ERCOT","ISO-NE","IESO","AESO"}
UA="continental-load-registry/source-health-monitor"

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest() if (ROOT/path).exists() else None

def parse_registry():
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    m=re.search(r"const REGISTRY_DATA = (\[.*?\]);\n",html,re.S)
    if not m: raise RuntimeError("REGISTRY_DATA not found")
    return json.loads(m.group(1))

def source_inventory():
    sm=load("data/source_manifest.json")["sources"]
    stack=load("data/track3_source_stack.json")["sources"]
    universe=load("data/external/epoch_ai/queue_source_universe.json")
    out={}
    for key,v in sm.items():
        u=v.get("official_source_url") or v.get("feed_url")
        out["manifest:"+key]={"id":key,"name":v.get("source_name"),"url":u,"publisher":v.get("publisher"),"mode":"AUTOMATED_ADAPTER" if key in AUTOMATED_ADAPTERS else "SNAPSHOT_OR_HEALTHCHECK_ONLY","workflow":AUTOMATED_ADAPTERS.get(key,[None,None])[0],"script":AUTOMATED_ADAPTERS.get(key,[None,None])[1],"local_file":v.get("source_file"),"declared_capture_date":v.get("capture_date")}
    for s in stack:
        key=s.get("id")
        if key in out: continue
        out["stack:"+str(key)]={"id":key,"name":s.get("name"),"url":s.get("url"),"publisher":None,"mode":"AUTOMATED_ADAPTER" if key in AUTOMATED_ADAPTERS else ("CATALOG_ONLY" if not s.get("url") else "HEALTHCHECK_ONLY"),"workflow":AUTOMATED_ADAPTERS.get(key,[None,None])[0],"script":AUTOMATED_ADAPTERS.get(key,[None,None])[1],"local_file":(s.get("snapshot_files") or [None])[0],"declared_capture_date":s.get("capture_on") or s.get("last_captured_utc")}
    for group in ("direct_queue_and_connection_sources","cross_cutting_public_sources"):
        for s in universe.get(group,[]):
            key="universe:"+str(s.get("id"))
            if key in out: continue
            out[key]={"id":s.get("id"),"name":s.get("name"),"url":s.get("url"),"publisher":s.get("authority"),"mode":"HEALTHCHECK_ONLY" if s.get("url") else "CATALOG_ONLY","workflow":None,"script":None,"local_file":None,"declared_capture_date":None}
    return list(out.values())

def http_fingerprint(url):
    if not url: return {"status":"NO_URL"}
    last=None
    for method,headers in (("HEAD",{}),("GET",{"Range":"bytes=0-65535"})):
        try:
            req=Request(url,method=method,headers={"User-Agent":UA,**headers})
            with urlopen(req,timeout=25) as r:
                body=r.read(65536) if method=="GET" else b""
                hdr={k.lower():v for k,v in r.headers.items()}
                fp={"status":"HEALTHY","http_status":r.status,"final_url":r.geturl(),"etag":hdr.get("etag"),"last_modified":hdr.get("last-modified"),"content_length":hdr.get("content-length"),"content_type":hdr.get("content-type"),"sample_sha256":hashlib.sha256(body).hexdigest() if body else None}
                return fp
        except (HTTPError,URLError,TimeoutError,ValueError) as exc:
            last=str(exc)
    return {"status":"FAILED","error":last}

def source_health(prev):
    results=[]; failed=[]; seen_urls=set()
    for s in source_inventory():
        if s.get("url") and s["url"] in seen_urls:
            continue
        if s.get("url"): seen_urls.add(s["url"])
        old=prev.get(s["url"],{}) if s.get("url") else {}
        fp=http_fingerprint(s.get("url"))
        changed=None
        if fp.get("status")=="HEALTHY" and old:
            old_tuple=(old.get("etag"),old.get("last_modified"),old.get("content_length"),old.get("sample_sha256"))
            new_tuple=(fp.get("etag"),fp.get("last_modified"),fp.get("content_length"),fp.get("sample_sha256"))
            changed=old_tuple!=new_tuple
        local_file=s.get("local_file")
        local_candidates=[]
        if local_file:
            local_candidates += [ROOT/"data"/local_file, ROOT/"data"/"external"/"epoch_ai"/local_file, ROOT/local_file]
        local_path=next((p for p in local_candidates if p.exists()),None)
        item={**s,"checked_at_utc":NOW_ISO,"fingerprint":fp,"changed_since_previous_check":changed,"local_artifact_present":local_path is not None,"local_artifact_path":str(local_path.relative_to(ROOT)).replace("\\","/") if local_path else None,"declared_sha256":None}
        if fp.get("status")=="FAILED":
            item["failure_class"]="REMOTE_SOURCE_UNAVAILABLE"
            failed.append(item)
        results.append(item)
    return results,failed

def queue_release_diff():
    current=parse_registry()
    snap_dir=AUTO/"queue_snapshots"; snap_dir.mkdir(parents=True,exist_ok=True)
    existing=sorted(snap_dir.glob("*.json"))
    previous=json.loads(existing[-1].read_text(encoding="utf-8")) if existing else None
    cur_by={str(x.get("id")):x for x in current}
    added=[]; removed=[]; changed=[]
    if previous:
        prev_by={str(x.get("id")):x for x in previous["records"]}
        added=[cur_by[k] for k in sorted(set(cur_by)-set(prev_by))]
        removed=[prev_by[k] for k in sorted(set(prev_by)-set(cur_by))]
        changed=[{"id":k,"before":prev_by[k],"after":cur_by[k]} for k in sorted(set(cur_by)&set(prev_by)) if cur_by[k]!=prev_by[k]]
    else:
        prev_by={}
        added=list(current)
    if previous:
        removed=[prev_by[k] for k in sorted(set(prev_by)-set(cur_by))]
        changed=[{"id":k,"before":prev_by[k],"after":cur_by[k]} for k in sorted(set(cur_by)&set(prev_by)) if cur_by[k]!=prev_by[k]]
    by_rto={}
    for r in current: by_rto.setdefault(r.get("rto"),{"current":0,"added":0,"removed":0,"changed":0})["current"]+=1
    if previous:
        prev_rto={}
        for r in previous["records"]: prev_rto.setdefault(r.get("rto"),{"current":0,"added":0,"removed":0,"changed":0})["current"]+=1
        for r in added: by_rto.setdefault(r.get("rto"),{"current":0,"added":0,"removed":0,"changed":0})["added"]+=1
        for r in removed: by_rto.setdefault(r.get("rto"),{"current":0,"added":0,"removed":0,"changed":0})["removed"]+=1
        for x in changed: by_rto.setdefault(x["after"].get("rto"),{"current":0,"added":0,"removed":0,"changed":0})["changed"]+=1
    snapshot={"schema_version":1,"captured_at_utc":NOW_ISO,"record_count":len(current),"registry_sha256":hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest(),"records":current}
    snap_path=snap_dir/f"{TODAY}.json"; snap_path.write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return {"schema_version":1,"generated_at_utc":NOW_ISO,"comparison_basis":previous.get("captured_at_utc") if previous else None,"current_record_count":len(current),"previous_record_count":len(previous["records"]) if previous else None,"added_count":len(added),"removed_count":len(removed),"changed_count":len(changed),"by_rto":by_rto,"added":added,"removed":removed,"changed":changed,"current_snapshot":str(snap_path.relative_to(ROOT)).replace("\\","/")}

def duplicate_report(records):
    by_id={}; by_exact={}; by_project={}
    for r in records:
        rid=str(r.get("id")); by_id.setdefault(rid,[]).append(r)
        sig=json.dumps([r.get("rto"),r.get("st"),r.get("co"),r.get("poi"),r.get("mw"),r.get("proj"),r.get("dev")],sort_keys=True)
        by_exact.setdefault(sig,[]).append(r)
        ps=(str(r.get("rto")),str(r.get("proj")),str(r.get("dev")),str(r.get("mw")))
        by_project.setdefault(ps,[]).append(r)
    def groups(d): return [v for v in d.values() if len(v)>1]
    return {"schema_version":1,"generated_at_utc":NOW_ISO,"record_count":len(records),"duplicate_id_groups":groups(by_id),"exact_duplicate_groups":groups(by_exact),"same_project_developer_mw_groups":groups(by_project)}

def geography_report(records):
    epoch=load("data/external/epoch_ai/registry.json")["records"]
    cross=(ROOT/"data/external/epoch_ai/crosswalk.csv")
    crows=list(csv.DictReader(cross.open("r",encoding="utf-8",newline=""))) if cross.exists() else []
    qstates=sum(bool(str(r.get("st") or "").strip()) for r in records)
    qcounties=sum(bool(str(r.get("co") or "").strip()) for r in records)
    ep_states=sum(bool(str(r.get("normalized",{}).get("country") or "").strip()) for r in epoch)
    cross_states=sum(bool(str(r.get("state_province") or "").strip()) for r in crows)
    return {"schema_version":1,"generated_at_utc":NOW_ISO,"queue_rows":len(records),"queue_rows_with_state":qstates,"queue_rows_with_county_or_zone":qcounties,"epoch_sites":len(epoch),"epoch_sites_with_country":ep_states,"crosswalk_rows":len(crows),"crosswalk_rows_with_state":cross_states,"geographic_join_method":"state/zone and stable Epoch ID crosswalk; no geocoding inference is introduced by this report"}

def evidence_quality():
    e=load("data/track3/evidence_records.json")["records"]
    missing_url=sum(not e1.get("source_url") for e1 in e)
    missing_target=sum(not e1.get("target_id") for e1 in e)
    missing_type=sum(not e1.get("evidence_type") for e1 in e)
    entity=load("data/track3/entity_resolution.json")
    return {"schema_version":1,"generated_at_utc":NOW_ISO,"evidence_records":len(e),"missing_source_url":missing_url,"missing_target_id":missing_target,"missing_evidence_type":missing_type,"entity_count":entity.get("stats",{}).get("entity_count"),"relationship_edges":entity.get("stats",{}).get("relationship_edge_count")}

def main():
    AUTO.mkdir(parents=True,exist_ok=True)
    prev={}
    hp=AUTO/"source_health.json"
    if hp.exists():
        try:
            prev={x.get("url"):x.get("fingerprint",{}) for x in load("data/automation/source_health.json").get("sources",[]) if x.get("url")}
        except Exception: prev={}
    sources,failed=source_health(prev)
    (AUTO/"source_registry.json").write_text(json.dumps({"schema_version":1,"generated_at_utc":NOW_ISO,"sources":sources},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (AUTO/"source_health.json").write_text(json.dumps({"schema_version":1,"generated_at_utc":NOW_ISO,"source_count":len(sources),"failed_count":len(failed),"sources":sources},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    diff=queue_release_diff(); (AUTO/"queue_release_diff.json").write_text(json.dumps(diff,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    dup=duplicate_report(parse_registry()); (AUTO/"duplicate_report.json").write_text(json.dumps(dup,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    geo=geography_report(parse_registry()); (AUTO/"geographic_match_report.json").write_text(json.dumps(geo,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    eq=evidence_quality(); (AUTO/"evidence_quality_report.json").write_text(json.dumps(eq,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    automated=[s for s in sources if s["mode"]=="AUTOMATED_ADAPTER"]
    adapter_gaps=[s for s in sources if s["mode"] in {"HEALTHCHECK_ONLY","SNAPSHOT_OR_HEALTHCHECK_ONLY"}]
    dq={"schema_version":1,"generated_at_utc":NOW_ISO,"summary":{"source_count":len(sources),"automated_adapter_sources":len(automated),"healthcheck_or_snapshot_only_sources":len(adapter_gaps),"remote_source_failures":len(failed),"automated_remote_source_failures":sum(1 for x in failed if x.get("mode")=="AUTOMATED_ADAPTER"),"queue_current_records":diff["current_record_count"],"queue_added":diff["added_count"],"queue_removed":diff["removed_count"],"queue_changed":diff["changed_count"],"duplicate_id_groups":len(dup["duplicate_id_groups"]),"exact_duplicate_groups":len(dup["exact_duplicate_groups"]),"evidence_records":eq["evidence_records"],"evidence_missing_urls":eq["missing_source_url"],"entity_count":eq["entity_count"],"relationship_edges":eq["relationship_edges"]},
      "automation_matrix":sources,"source_failures":failed,"checks":{"source_change_detection":"ENABLED","queue_release_diff":"ENABLED","duplicate_detection":"ENABLED","geographic_matching":"ENABLED","evidence_extraction":"ENABLED_EXISTING_BUILDERS","entity_resolution":"ENABLED_EXISTING_PIPELINE","validation":"ENABLED_EXISTING_VALIDATORS","failed_source_alerts":"WORKFLOW_ISSUE_ALERTS"}}
    (AUTO/"data_quality_report.json").write_text(json.dumps(dq,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (AUTO/"automation_status.json").write_text(json.dumps({"schema_version":1,"generated_at_utc":NOW_ISO,"status":"SOURCE_HEALTH_CHECKED","next_stage":"existing source-specific sync workflows refresh automated adapters; this control plane detects changes/failures and validates downstream joins","source_count":len(sources),"automated_adapter_sources":len(automated),"healthcheck_or_snapshot_only_sources":len(adapter_gaps),"failed_sources":len(failed),"queue_release_diff":True,"duplicate_detection":True,"geographic_matching":True,"evidence_quality":True,"entity_resolution":True},indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dq["summary"],indent=2))
    # Fail only on unavailable sources that the repository claims have an automated adapter.
    automated_failures=[x for x in failed if x["mode"]=="AUTOMATED_ADAPTER"]
    return 1 if automated_failures else 0

if __name__=="__main__": raise SystemExit(main())
