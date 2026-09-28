#!/usr/bin/env python3
"""Build normalized claim-level Track 3 artifact from public-web enrichment."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=ROOT/"data/track3/public_web_enrichment_2026-09-27.json"
OUT=ROOT/"data/track3/public_web_claims.json"
DOMAIN_MAP={"site_identity":"site_identity","address":"site_identity","location":"site_identity","project":"site_identity","project_status":"site_identity","operational_status":"site_identity","owner":"ownership","investors":"financing","investment":"financing","capex_record":"financing","construction_companies":"construction","construction_status":"construction","construction_workforce_record":"construction","chip_quantities":"chip_inventory","users":"compute_tenancy","capacity_record":"capacity","service_or_contract":"service_or_contract","regulatory":"regulatory","energy_companies":"grid_connection","cooling":"cooling","backup_generation":"power_telemetry","operational_efficiency":"operations","chip_ownership":"chip_ownership","chip_shipments":"chip_shipments","chip_users":"chip_users"}
def main()->int:
    d=json.loads(SRC.read_text(encoding="utf-8"))
    claims=[]
    for i,x in enumerate(d.get("records",[]),1):
        claims.append({
            "claim_id":x.get("evidence_id") or f"PWEB-CLAIM-{i:04d}",
            "epoch_id":x.get("epoch_id"),
            "site_name":x.get("site_name"),
            "domain":DOMAIN_MAP.get(x.get("field"),"other"),
            "field":x.get("field"),
            "value":x.get("value"),
            "relationship":x.get("relationship"),
            "source":x.get("source"),
            "source_urls":x.get("source_urls") or [],
            "publication_date":x.get("publication_date"),
            "capture_date":x.get("capture_date"),
            "disposition":x.get("disposition") or "PUBLIC_SOURCE_CAPTURED",
            "scope_note":x.get("scope_note"),
            "claim_scope":"site_level_public_web",
            "provenance_status":"source_link_retained",
            "source_record_id":x.get("evidence_id"),
        })
    out={"schema_version":1,"generated_on":"2026-09-27","title":"Track 3 public-web claim layer","purpose":"Normalized claim-level representation of the public-web enrichment layer.","accounting":{"claim_count":len(claims),"site_count":len({x["epoch_id"] for x in claims}),"domain_counts":{}}, "claims":claims}
    for x in claims: out["accounting"]["domain_counts"][x["domain"]]=out["accounting"]["domain_counts"].get(x["domain"],0)+1
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(out["accounting"],indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
