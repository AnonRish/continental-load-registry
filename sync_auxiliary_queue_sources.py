#!/usr/bin/env python3
"""Capture public queue/connection sources that do not yet have dedicated normalized adapters.

This is a raw-source ingestion layer:
- ERCOT GIS workbook: captured and, where parsing is available, normalized.
- ISO-NE external reports: HTML snapshot captured.
- IESO Application Status: HTML snapshot captured.
- AESO Connection Project List: XLSX snapshot captured.

Raw capture is explicitly distinct from successful site-level parsing.
"""
from __future__ import annotations
import hashlib,json,io
from datetime import datetime,timezone
from pathlib import Path
import requests,pandas as pd

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"data"/"automation"/"auxiliary_sources"; NOW=datetime.now(timezone.utc).isoformat()
UA="continental-load-registry/auxiliary-source-capture"
TIMEOUT=90

SOURCES={
 "ERCOT-GIS":{"kind":"workbook_discovery","url":"https://www.ercot.com/mp/data-products/data-product-details?id=pg7-200-er","output":"ercot_gis_source.bin"},
 "ISO-NE":{"kind":"html","url":"https://irtt.iso-ne.com/reports/external","output":"iso_ne_public_queue.html"},
 "IESO":{"kind":"html","url":"https://ieso.ca/Sector-Participants/Connection-Process/Application-Status","output":"ieso_application_status.html"},
 "AESO":{"kind":"xlsx","url":"https://www.aeso.ca/assets/Uploads/project-reporting/September-2026-Project-List.xlsx","output":"aeso_connection_project_list.xlsx"},
}

def get(url):
    r=requests.get(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"},timeout=TIMEOUT)
    r.raise_for_status()
    if not r.content: raise RuntimeError("empty response")
    return r

def capture_direct(sid,spec):
    r=get(spec["url"])
    path=OUT/spec["output"]; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(r.content)
    item={"source_id":sid,"url":spec["url"],"captured_at_utc":NOW,"http_status":r.status_code,"bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest(),"content_type":r.headers.get("Content-Type"),"status":"RAW_CAPTURED","path":str(path.relative_to(ROOT)).replace("\\","/")}
    if sid=="ISO-NE":
        try:
            tables=pd.read_html(io.StringIO(r.text))
            item["table_count"]=len(tables); item["table_row_counts"]=[len(t) for t in tables]
        except Exception as exc: item["table_parse_error"]=str(exc)
    elif sid=="IESO":
        try:
            tables=pd.read_html(io.StringIO(r.text))
            item["table_count"]=len(tables); item["table_row_counts"]=[len(t) for t in tables]
        except Exception as exc: item["table_parse_error"]=str(exc)
    elif sid=="AESO":
        try:
            sheets=pd.read_excel(io.BytesIO(r.content),sheet_name=None)
            item["sheet_names"]=list(sheets); item["sheet_row_counts"]={k:len(v) for k,v in sheets.items()}
            normalized=[]
            for name,df in sheets.items():
                normalized.append({"sheet":name,"columns":[str(x) for x in df.columns],"rows":len(df)})
            item["normalized_sheet_catalog"]=normalized
        except Exception as exc: item["parse_error"]=str(exc)
    return item

def capture_ercot():
    # Reuse the researched, source-specific discovery/HTTP logic.
    import ingest_grid_queues as g
    session=g.build_http_session()
    data=g.fetch_ercot_gis_workbook(session)
    path=OUT/SOURCES["ERCOT-GIS"]["output"]; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    return {"source_id":"ERCOT-GIS","url":SOURCES["ERCOT-GIS"]["url"],"captured_at_utc":NOW,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"status":"RAW_CAPTURED","path":str(path.relative_to(ROOT)).replace("\\","/"),"discovery_method":"ingest_grid_queues.fetch_ercot_gis_workbook"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    try: results.append(capture_ercot())
    except Exception as exc: results.append({"source_id":"ERCOT-GIS","status":"FAILED","error":str(exc),"url":SOURCES["ERCOT-GIS"]["url"],"captured_at_utc":NOW})
    for sid in ("ISO-NE","IESO","AESO"):
        try: results.append(capture_direct(sid,SOURCES[sid]))
        except Exception as exc: results.append({"source_id":sid,"status":"FAILED","error":str(exc),"url":SOURCES[sid]["url"],"captured_at_utc":NOW})
    out={"schema_version":1,"generated_at_utc":NOW,"source_count":len(results),"failed_count":sum(x["status"]=="FAILED" for x in results),"sources":results}
    (OUT/"manifest.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))
    return 1 if out["failed_count"] else 0
if __name__=="__main__": raise SystemExit(main())
