#!/usr/bin/env python3
"""Download and normalize CAISO's complete public interconnection queue workbook.

This is a separate universe from the conservative large-load registry. It preserves
the three public CAISO queue sheets (active/current, completed and withdrawn) and
keeps both normalized fields and the original row as JSON so no source field is
silently discarded.
"""
from __future__ import annotations

import argparse, io, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

SOURCE_URL = "https://www.caiso.com/documents/publicqueuereport.xlsx"
SHEETS = {
    "Grid GenerationQueue": "active",
    "Completed Generation Projects": "completed",
    "Withdrawn Generation Projects": "withdrawn",
}
USER_AGENT = "Continental-Large-Load-Registry/1.0 (public research ETL)"

ALIASES = {
    "queue_id": ["Queue Position", "Interconnection Queue Position", "Queue ID"],
    "project_name": ["Project Name", "Project Name - Confidential"],
    "receive_date": ["Interconnection Request Receive Date"],
    "queue_date": ["Queue Date"],
    "application_status": ["Application Status"],
    "study_process": ["Study Process", "Study Type"],
    "mw_total": ["MW Total", "Net MWs to Grid", "Net MW"],
    "deliverability_status": ["Full Capacity, Partial or Energy Only (FC/P/EO)", "Deliverability Status"],
    "county": ["County", "Location"],
    "state": ["State"],
    "utility": ["Utility"],
    "pto_region": ["PTO Study Region", "PTO Region"],
    "station_or_line": ["Station or Transmission Line", "Interconnection Location", "Point of Interconnection"],
    "proposed_online_date": ["Proposed On-line Date (as filed with IR)", "Proposed On-line Date"],
    "current_online_date": ["Current On-line Date"],
    "suspension_status": ["Suspension Status"],
    "feasibility_status": ["Feasibility Study or Supplemental Review"],
    "system_impact_status": ["System Impact Study or Phase I Cluster Study"],
    "facilities_status": ["Facilities Study (FAS) or Phase II Cluster Study"],
    "optional_study_status": ["Optional Study (OS)"],
    "ia_status": ["Interconnection Agreement Status"],
    "withdrawal_reason": ["Reason for Withdrawal"],
}

def clean_col(x: Any) -> str:
    s = str(x or "").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()

def json_value(v: Any) -> Any:
    if pd.isna(v):
        return None
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.isoformat()
    if hasattr(v, "item"):
        try:
            return json_value(v.item())
        except Exception:
            pass
    return v

def find_col(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {clean_col(c).lower(): c for c in columns}
    for alias in aliases:
        a = clean_col(alias).lower()
        if a in normalized:
            return normalized[a]
    for alias in aliases:
        a = clean_col(alias).lower()
        for c in columns:
            if a in clean_col(c).lower() or clean_col(c).lower() in a:
                return c
    return None

def normalize_sheet(frame: pd.DataFrame, sheet: str) -> list[dict[str, Any]]:
    frame = frame.copy()
    frame.columns = [clean_col(c) for c in frame.columns]
    frame = frame.dropna(how="all").copy()
    # The workbook carries a legend block after the project table. Remove rows
    # after the last row containing either a project name or queue position.
    pcol = find_col(list(frame.columns), ALIASES["project_name"])
    qcol = find_col(list(frame.columns), ALIASES["queue_id"])
    if pcol or qcol:
        meaningful = pd.Series(False, index=frame.index)
        if pcol:
            meaningful |= frame[pcol].notna() & frame[pcol].astype(str).str.strip().ne("")
        if qcol:
            meaningful |= frame[qcol].notna() & frame[qcol].astype(str).str.strip().ne("")
        if meaningful.any():
            frame = frame.loc[: meaningful[meaningful].index[-1]]
    out: list[dict[str, Any]] = []
    cols = list(frame.columns)
    for source_row_number, (_, row) in enumerate(frame.iterrows(), start=5):
        raw = {c: json_value(row[c]) for c in cols}
        if not any(v is not None and str(v).strip() for v in raw.values()):
            continue
        normalized: dict[str, Any] = {"source_sheet": sheet}
        for key, aliases in ALIASES.items():
            c = find_col(cols, aliases)
            normalized[key] = json_value(row[c]) if c else None
        # Numeric MW, when present and parseable.
        try:
            normalized["mw_total"] = float(normalized["mw_total"]) if normalized["mw_total"] is not None else None
        except Exception:
            normalized["mw_total"] = None
        out.append({
            "source_sheet": sheet,
            "source_row_number": source_row_number,
            "status_class": SHEETS[sheet],
            "normalized": normalized,
            "raw": raw,
        })
    return out

def download() -> bytes:
    response = requests.get(SOURCE_URL, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    if not response.content[:2] == b"PK":
        raise RuntimeError("CAISO response did not look like an XLSX/ZIP workbook")
    return response.content

def build(payload: bytes) -> dict[str, Any]:
    sheets = pd.read_excel(io.BytesIO(payload), skiprows=3, sheet_name=None)
    records: list[dict[str, Any]] = []
    sheet_counts: dict[str, int] = {}
    for sheet_name, status in SHEETS.items():
        if sheet_name not in sheets:
            raise RuntimeError(f"Expected CAISO sheet missing: {sheet_name}")
        rows = normalize_sheet(sheets[sheet_name], sheet_name)
        records.extend(rows)
        sheet_counts[sheet_name] = len(rows)
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "title": "CAISO complete public interconnection queue",
        "source_url": SOURCE_URL,
        "captured_at": captured_at,
        "source_note": "Official CAISO Public Queue Report workbook. The source contains current active, completed and withdrawn interconnection-request sheets. Rows are preserved with original source fields and a normalized subset.",
        "accounting": "Separate generator-interconnection universe; not added to the conservative large-load core total. Coordinates are derived only in the browser from the published county/state fields.",
        "sheet_counts": sheet_counts,
        "record_count": len(records),
        "records": records,
    }

def selftest() -> None:
    cols = [
        "Project Name", "Queue Position", "MW Total", "County", "State", "Utility",
        "Study Process", "Application Status", "Interconnection Agreement Status"
    ]
    frame = pd.DataFrame([
        ["TEST PROJECT", 1234, 150.0, "KERN", "CA", "SCE", "Serial LGIP", "ACTIVE", "Executed"],
        [None, None, None, None, None, None, None, None, None],
        ["Legend text", None, None, None, None, None, None, None, None],
    ], columns=cols)
    rows = normalize_sheet(frame, "Grid GenerationQueue")
    assert len(rows) == 1
    assert rows[0]["normalized"]["project_name"] == "TEST PROJECT"
    assert rows[0]["normalized"]["mw_total"] == 150.0
    assert rows[0]["raw"]["Utility"] == "SCE"
    print("PASS: CAISO parser self-test")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--output-dir", default="data")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    payload = download()
    data = build(payload)
    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    # Build the JSON snapshot first; summary is included in the same object so the browser
    # can render counts without a second request.
    summary = {
        "record_count": data["record_count"],
        "sheet_counts": data["sheet_counts"],
        "mw_rows": sum(r["normalized"].get("mw_total") is not None for r in data["records"]),
        "records_ge_100mw": sum((r["normalized"].get("mw_total") or 0) >= 100 for r in data["records"]),
        "records_with_county_and_state": sum(bool(r["normalized"].get("county")) and bool(r["normalized"].get("state")) for r in data["records"]),
    }
    data["summary"] = summary
    (root / "caiso_public_queue.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = []
    for rec in data["records"]:
        n = rec["normalized"].copy()
        n["status_class"] = rec["status_class"]
        n["source_row_number"] = rec["source_row_number"]
        n["raw_record_json"] = json.dumps(rec["raw"], ensure_ascii=False, separators=(",", ":"))
        rows.append(n)
    pd.DataFrame(rows).to_csv(root / "caiso_public_queue.csv", index=False)
    summary = {
        "source_url": SOURCE_URL,
        "captured_at": data["captured_at"],
        "record_count": data["record_count"],
        "sheet_counts": data["sheet_counts"],
        "mw_rows": sum(r["normalized"].get("mw_total") is not None for r in data["records"]),
        "records_ge_100mw": sum((r["normalized"].get("mw_total") or 0) >= 100 for r in data["records"]),
        "records_with_county_and_state": sum(bool(r["normalized"].get("county")) and bool(r["normalized"].get("state")) for r in data["records"]),
    }
    (root / "caiso_public_queue_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
