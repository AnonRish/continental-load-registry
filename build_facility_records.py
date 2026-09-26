#!/usr/bin/env python3
"""
Build per-RTO facility research records from the published registry plus retained
raw/enriched CSV artifacts.

The output is static JSON designed for GitHub Pages. Every record contains:
  * the normalized registry fields available for that row;
  * the exact retained raw CSV values when a raw artifact exists;
  * official source/capture metadata;
  * a compact provenance trail describing source -> ingest -> enrichment -> publication.

Missing raw captures are represented explicitly as unavailable; this script never
reconstructs an "original raw value" from a normalized value and calls it raw.

Examples:
  python build_facility_records.py --check
  python build_facility_records.py --capture-date 2026-09-26 --check
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

DATA_RE = re.compile(r"const REGISTRY_DATA = (\[.*?\]);\n", re.S)

NORMALIZED_KEYS = [
    "queue_id", "rto_region", "state_province", "county_or_zone",
    "poi_substation", "capacity_mw", "projected_date", "status",
    "project_name", "developer_entity", "raw_fuel_technology",
    "entity_category", "matched_public_entity", "entity_match_score",
    "load_type_tier", "transmission_owner", "in_known_high_density_zone",
    "project_name_keyword_hits", "reached_ia_stage",
    "gpus_estimate_low", "gpus_estimate_reference", "gpus_estimate_high",
    "run_flops_90d_low", "run_flops_90d_reference", "run_flops_90d_high",
    "clears_1e26_flops_all_scenarios", "review_priority", "review_reason",
]

NUMERIC_KEYS = {
    "capacity_mw", "entity_match_score",
    "gpus_estimate_low", "gpus_estimate_reference", "gpus_estimate_high",
    "run_flops_90d_low", "run_flops_90d_reference", "run_flops_90d_high",
}
BOOL_KEYS = {
    "in_known_high_density_zone", "reached_ia_stage",
    "clears_1e26_flops_all_scenarios", "review_priority",
}

RAW_FIELDS = [
    "queue_id", "rto_region", "state", "county", "poi_substation",
    "capacity_mw", "projected_date", "developer_entity", "status",
    "project_name", "raw_fuel_technology",
]

def read_csv(path: Path) -> tuple[list[dict[str, str]], str]:
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    text = data.decode("utf-8-sig")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows, sha

def blank_to_none(value: Any) -> Any:
    if value is None:
        return None
    s = str(value)
    return None if s.strip() == "" else s

def coerce(key: str, value: Any) -> Any:
    value = blank_to_none(value)
    if value is None:
        return None
    if key in BOOL_KEYS:
        return str(value).strip().lower() in {"true", "1", "yes"}
    if key in NUMERIC_KEYS:
        return float(value) if key.startswith(("run_", "entity_")) else int(float(value)) if key.startswith("gpus_") else float(value)
    return value

def compute_range(mw: float) -> dict[str, Any]:
    def run(pue: float, kw_per_rack: float, mfu: float) -> tuple[int, float]:
        gpus = (mw * 1000.0 / pue / kw_per_rack) * 8
        flops = gpus * 1979.0e12 * (90 * 86400) * mfu
        return round(gpus), flops
    low_gpu, low_flops = run(1.4, 20.0, 0.25)
    high_gpu, high_flops = run(1.15, 50.0, 0.50)
    return {
        "gpus_estimate_low": low_gpu,
        "gpus_estimate_high": high_gpu,
        "run_flops_90d_low": low_flops,
        "run_flops_90d_high": high_flops,
        "clears_1e26_flops_all_scenarios": low_flops >= 1e26,
    }

def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def load_registry(path: Path) -> list[dict[str, Any]]:
    html = path.read_text(encoding="utf-8")
    match = DATA_RE.search(html)
    if not match:
        raise SystemExit(f"no REGISTRY_DATA array found in {path}")
    return json.loads(match.group(1))

def source_ref(manifest_entry: dict[str, Any], rto: str, capture_date: str | None = None) -> dict[str, Any]:
    out = dict(manifest_entry)
    if capture_date:
        out["capture_date"] = capture_date
        out["capture_precision"] = "day"
        out["capture_basis"] = "Primary raw artifact supplied to this build command; date passed by the publication pipeline."
    return out

def make_record(
    row: dict[str, Any],
    raw_row: dict[str, str] | None,
    enriched_row: dict[str, str] | None,
    source: dict[str, Any],
    raw_artifact: dict[str, Any] | None,
) -> dict[str, Any]:
    mw = float(row["mw"])
    calc = compute_range(mw)
    normalized: dict[str, Any] = {
        "queue_id": row["id"],
        "rto_region": row["rto"],
        "state_province": row["st"],
        "county_or_zone": row["co"],
        "poi_substation": row["poi"],
        "capacity_mw": mw,
        "projected_date": raw_row.get("projected_date") if raw_row else None,
        "status": row["status"],
        "project_name": row["proj"] or None,
        "developer_entity": row["dev"] or None,
        "raw_fuel_technology": raw_row.get("raw_fuel_technology") if raw_row else None,
        "entity_category": row["ent"] or None,
        "matched_public_entity": None,
        "entity_match_score": None,
        "load_type_tier": row["tier"] or None,
        "transmission_owner": None,
        "in_known_high_density_zone": None,
        "project_name_keyword_hits": None,
        "reached_ia_stage": None,
        "gpus_estimate_low": calc["gpus_estimate_low"],
        "gpus_estimate_reference": int(row["gpu"]),
        "gpus_estimate_high": calc["gpus_estimate_high"],
        "run_flops_90d_low": calc["run_flops_90d_low"],
        "run_flops_90d_reference": float(row["flops"]),
        "run_flops_90d_high": calc["run_flops_90d_high"],
        "clears_1e26_flops_all_scenarios": calc["clears_1e26_flops_all_scenarios"],
        "review_priority": bool(row["flag"]),
        "review_reason": None,
    }

    if enriched_row:
        for key in NORMALIZED_KEYS:
            if key in enriched_row and key not in {
                "queue_id", "rto_region", "state", "county", "capacity_mw"
            }:
                if key == "state":
                    continue
                normalized[key] = coerce(key, enriched_row.get(key))
        normalized["state_province"] = row["st"]
        normalized["county_or_zone"] = row["co"]
        normalized["poi_substation"] = row["poi"]
        normalized["projected_date"] = raw_row.get("projected_date") if raw_row else None
        normalized["capacity_mw"] = mw
        normalized["queue_id"] = row["id"]
        normalized["rto_region"] = row["rto"]

    if normalized.get("gpus_estimate_low") is None:
        normalized["gpus_estimate_low"] = calc["gpus_estimate_low"]
    if normalized.get("gpus_estimate_high") is None:
        normalized["gpus_estimate_high"] = calc["gpus_estimate_high"]
    if normalized.get("run_flops_90d_low") is None:
        normalized["run_flops_90d_low"] = calc["run_flops_90d_low"]
    if normalized.get("run_flops_90d_high") is None:
        normalized["run_flops_90d_high"] = calc["run_flops_90d_high"]
    if normalized.get("clears_1e26_flops_all_scenarios") is None:
        normalized["clears_1e26_flops_all_scenarios"] = calc["clears_1e26_flops_all_scenarios"]
    normalized["review_priority"] = bool(row["flag"])

    available_normalized = [k for k in NORMALIZED_KEYS if normalized.get(k) is not None]
    raw_status = "retained_csv_row" if raw_row else "not_retained"
    raw_values = dict(raw_row) if raw_row else {}

    provenance = [
        {
            "stage": "source",
            "description": f"Publisher source: {source.get('source_name', 'official source')}.",
            "official_source_url": source.get("official_source_url"),
        },
        {
            "stage": "raw_capture",
            "description": (
                "Original source row is retained in a repository CSV artifact."
                if raw_row
                else "Original source row is not retained in the repository; raw values are not reconstructed."
            ),
            "artifact": raw_artifact,
        },
        {
            "stage": "normalization",
            "script": "ingest_grid_queues.py",
            "description": "Shared queue schema, source-specific filtering, location normalization, and status handling.",
        },
        {
            "stage": "enrichment",
            "script": "compute_anomaly_detector.py",
            "description": (
                "Retained enrichment fields from the committed enriched CSV."
                if enriched_row
                else "Only the embedded reference fields were retained; low/high compute-range fields are recomputed from normalized MW using the documented scenario constants."
            ),
        },
        {
            "stage": "publication",
            "script": "embed_registry_data.py",
            "description": "Published dashboard row plus this per-RTO research-record JSON artifact.",
        },
    ]

    return {
        "schema_version": 1,
        "record_id": row["id"],
        "normalized": normalized,
        "available_normalized_fields": available_normalized,
        "raw": {
            "availability": raw_status,
            "source_columns": list(raw_row.keys()) if raw_row else [],
            "values": raw_values,
        },
        "source": source,
        "provenance": provenance,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", type=Path, default=Path("index.html"))
    ap.add_argument("--raw", type=Path, action="append", default=[])
    ap.add_argument("--enriched", type=Path, action="append", default=[])
    ap.add_argument("--source-manifest", type=Path, default=Path("data/source_manifest.json"))
    ap.add_argument("--output-dir", type=Path, default=Path("data/facility_records"))
    ap.add_argument("--capture-date", default=None, help="Override capture date for RTOs present in the first --raw file.")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    registry = load_registry(args.html)
    manifest = load_manifest(args.source_manifest)
    raw_paths = args.raw or [Path("data/registry_raw.csv"), Path("data/registry_raw_new5.csv")]
    enriched_paths = args.enriched or [Path("data/computational_load_estimates.csv")]

    raw_by_key: dict[tuple[str, str], dict[str, str]] = {}
    raw_artifacts: dict[str, dict[str, Any]] = {}
    fresh_rtos: set[str] = set()
    for idx, path in enumerate(raw_paths):
        rows, sha = read_csv(path)
        artifact = {"path": path.as_posix(), "sha256": sha}
        raw_artifacts[path.as_posix()] = artifact
        for item in rows:
            key = (item.get("rto_region", ""), item.get("queue_id", ""))
            raw_by_key.setdefault(key, item)
        if idx == 0:
            fresh_rtos = {r.get("rto_region", "") for r in rows if r.get("rto_region")}

    enriched_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for path in enriched_paths:
        rows, sha = read_csv(path)
        for item in rows:
            key = (item.get("rto_region", ""), item.get("queue_id", ""))
            enriched_by_key.setdefault(key, item)
        raw_artifacts[path.as_posix()] = {"path": path.as_posix(), "sha256": sha}

    by_rto: dict[str, list[dict[str, Any]]] = {}
    for row in registry:
        rto = row["rto"]
        src_manifest = manifest["sources"].get(rto)
        if src_manifest is None:
            raise SystemExit(f"missing source manifest entry for {rto}")
        source = source_ref(
            src_manifest,
            rto,
            capture_date=args.capture_date if rto in fresh_rtos else None,
        )
        key = (rto, row["id"])
        raw_row = raw_by_key.get(key)
        enriched_row = enriched_by_key.get(key)
        raw_artifact = None
        if raw_row:
            # Prefer the first raw artifact whose keyed data supplied this row.
            for path in raw_paths:
                rows, _ = read_csv(path)
                if any(x.get("rto_region") == rto and x.get("queue_id") == row["id"] for x in rows):
                    raw_artifact = raw_artifacts[path.as_posix()]
                    break
        by_rto.setdefault(rto, []).append(
            make_record(row, raw_row, enriched_row, source, raw_artifact)
        )

    expected_counts: dict[str, int] = {}
    for row in registry:
        expected_counts[row["rto"]] = expected_counts.get(row["rto"], 0) + 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for rto, records in sorted(by_rto.items()):
        payload = {
            "schema_version": 1,
            "rto": rto,
            "record_count": len(records),
            "field_catalog": {
                "normalized_fields": NORMALIZED_KEYS,
                "raw_fields_when_retained": RAW_FIELDS,
            },
            "records": records,
        }
        (args.output_dir / f"{rto}.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    index = {
        "schema_version": 1,
        "generated_from": args.html.as_posix(),
        "record_count": len(registry),
        "rto_counts": expected_counts,
        "files": {rto: f"data/facility_records/{rto}.json" for rto in sorted(by_rto)},
    }
    (args.output_dir / "index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )

    if args.check:
        actual_total = sum(len(v) for v in by_rto.values())
        if actual_total != len(registry):
            raise SystemExit(f"record count mismatch: {actual_total} != {len(registry)}")
        ids = [r["record_id"] for records in by_rto.values() for r in records]
        if len(ids) != len(set(ids)):
            raise SystemExit("duplicate record IDs detected")
        if set(by_rto) != set(manifest["sources"]):
            raise SystemExit(f"RTO manifest mismatch: records={sorted(by_rto)} manifest={sorted(manifest['sources'])}")
        for rto, records in by_rto.items():
            if len(records) != expected_counts[rto]:
                raise SystemExit(f"{rto}: count mismatch")
            for rec in records:
                n = rec["normalized"]
                for key in ("queue_id", "rto_region", "state_province", "capacity_mw", "status"):
                    if n.get(key) in (None, ""):
                        raise SystemExit(f"{rto}/{rec['record_id']}: missing required normalized field {key}")
        print(f"CHECK OK: {actual_total} unique facility records across {len(by_rto)} RTOs")
        for rto in sorted(by_rto):
            retained = sum(1 for r in by_rto[rto] if r["raw"]["availability"] == "retained_csv_row")
            print(f"{rto:7s} {len(by_rto[rto]):4d} records · raw retained {retained:4d}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
