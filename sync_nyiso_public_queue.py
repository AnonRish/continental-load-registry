#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime,io,json
from pathlib import Path
import pandas as pd,requests
URL="https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx"
SHEETS={"Interconnection Queue":"active"," Cluster Projects":"cluster_active","Withdrawn":"withdrawn","Cluster Projects-Withdrawn":"cluster_withdrawn","In Service":"in_service"}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--selftest",action="store_true");ap.add_argument("--output-dir",default="data");a=ap.parse_args()
    if a.selftest:
        assert len(SHEETS)==5
        print("PASS: NYISO parser self-test");return
    r=requests.get(URL,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153 Safari/537.36","Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream;q=0.9,*/*;q=0.8","Referer":"https://www.nyiso.com/interconnections"},timeout=90);r.raise_for_status();book=pd.ExcelFile(io.BytesIO(r.content));recs=[]
    for sheet,status in SHEETS.items():
        if sheet not in book.sheet_names:raise RuntimeError(f"missing sheet: {sheet}")
        df=pd.read_excel(book,sheet_name=sheet,header=[0,1] if sheet=="In Service" else 0).dropna(how="all")
        if getattr(df.columns,"nlevels",1)>1:df.columns=[" ".join(str(x) for x in c if str(x)!="nan").strip() for c in df.columns]
        else:df.columns=[str(c).strip() for c in df.columns]
        for i,(_,row) in enumerate(df.iterrows(),1):
            raw={str(k):(None if pd.isna(v) else v.isoformat() if isinstance(v,(datetime.datetime,pd.Timestamp)) else v.item() if hasattr(v,"item") else v) for k,v in row.items()}
            def g(*ks):
                for k in ks:
                    if k in raw:return raw[k]
                return None
            q=g("Queue Pos.");name=g("Project Name")
            if q is None and name is None:continue
            vals=[]
            for k in ("SP (MW)","WP (MW)"):
                try:vals.append(float(g(k)))
                except Exception:pass
            recs.append({"source_sheet":sheet,"status_class":status,"source_row_number":i,"normalized":{"queue_id":q,"project_name":name,"developer_name":g("Developer Name","Owner/Developer"),"date_of_ir":g("Date of IR"),"summer_mw":g("SP (MW)"),"winter_mw":g("WP (MW)"),"capacity_mw":max(vals) if vals else None,"type_fuel":g("Type/ Fuel","Type/Fuel"),"county":g("County"),"state":g("State"),"interconnection_point":g("Interconnection Point","Points of Interconnection"),"utility":g("Utility"),"status":status,"last_updated":g("Last Updated Date","Last Update"),"proposed_in_service":g("Proposed In-Service Date","Proposed  In-Service"),"proposed_cod":g("Proposed COD"),"availability_of_studies":g("Availability of Studies"),"ia_status":g("S")},"raw":raw})
    root=Path(a.output_dir);root.mkdir(parents=True,exist_ok=True);now=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    obj={"schema_version":1,"title":"NYISO complete public interconnection queue","source_url":URL,"captured_at":now,"accounting":"Complete public NYISO interconnection queue layer; not added to conservative large-load core.","record_count":len(recs),"records":recs}
    (root/"nyiso_public_queue.json").write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    flat=[]
    for z in recs:
        q=z["normalized"].copy();q.update({"source_sheet":z["source_sheet"],"status_class":z["status_class"],"source_row_number":z["source_row_number"],"raw_record_json":json.dumps(z["raw"],ensure_ascii=False,separators=(",",":"))});flat.append(q)
    pd.DataFrame(flat).to_csv(root/"nyiso_public_queue.csv",index=False)
    s={"source_url":URL,"captured_at":now,"record_count":len(recs),"records_ge_100mw":sum((z["normalized"].get("capacity_mw") or 0)>=100 for z in recs)}
    (root/"nyiso_public_queue_summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");print(json.dumps(s,indent=2))
if __name__=="__main__":main()
