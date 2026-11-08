#!/usr/bin/env python3
"""Keep every copied count in the public artifacts equal to the file it describes.

Many artifacts repeat a number that is owned by another file -- the registry row
count lives in index.html, the MISO queue size in miso_public_queue_summary.json,
and so on. Sync jobs change the owning file every day, so each copy is rewritten
here from its owner instead of being edited by hand:

  owner                                         copies refreshed
  index.html REGISTRY_DATA                      large_load_scope, map_layer_manifest(.csv),
                                                market_universe_manifest, public_data_catalog
  data/*_public_queue_summary.json              queue_layer_status, map_layer_manifest(.csv),
                                                large_load_scope
  project / supplemental / BPA / Epoch layers   the same manifests and the catalog
  JSON ledgers                                  their CSV exports (see CSV_EXPORTS)

    python refresh_derived_counts.py          # rewrite every drifted copy
    python refresh_derived_counts.py --check  # report drift and exit 1; writes nothing
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REGISTRY_RE = re.compile(r"const REGISTRY_DATA = (\[.*?\]);\n", re.S)

# Queue-layer ids used across the manifests, keyed to the RTO feed that owns them.
QUEUE_LAYERS = {
    "MISO_COMPLETE_QUEUE": "MISO",
    "SPP_ACTIVE_QUEUE": "SPP",
    "CAISO_COMPLETE_QUEUE": "CAISO",
    "PJM_CYCLE_QUEUE": "PJM",
}
QUEUE_SUMMARIES = {
    "CAISO": "caiso_public_queue_summary.json",
    "MISO": "miso_public_queue_summary.json",
    "SPP": "spp_public_queue_summary.json",
    "PJM": "pjm_cycle_public_queue_summary.json",
}
# Registry RTO label -> market_universe_manifest id.
MARKET_IDS = {"IESO": "IESO_ON"}

# JSON ledgers whose CSV companion is a flat export of one record list. The CSV keeps
# its existing column set; list values are joined with " | " and *_json columns hold
# the JSON of the field without the suffix.
CSV_EXPORTS = {
    "data/miso_unresolved_large_loads.csv": ("data/miso_unresolved_large_loads.json", "records"),
    "data/project_level_map.csv": ("data/project_level_map.json", "records"),
    "data/supplemental_aggregate_map.csv": ("data/supplemental_aggregate_map.json", "records"),
    "data/track3/public_web_enrichment_2026-09-27.csv": ("data/track3/public_web_enrichment_2026-09-27.json", "records"),
    "data/track3/transformer_supply_chain_events.csv": ("data/track3/transformer_supply_chain_events.json", "records"),
    "data/market_universe_manifest.csv": ("data/market_universe_manifest.json", "markets"),
}
# Catalog entries whose count has a documented meaning that is not a row count.
STATIC_CATALOG_COUNTS = {
    # 435 = projects in the 2024 cluster report (Clusters <=8 through 14); the
    # 2026 Cluster 15 subset is a separate row of the same file.
    "data/caiso_cluster_history.json",
}
KEY_COLUMNS = ("evidence_id", "event_id", "queue_id", "id", "epoch_id")
# A carried-forward value is only reused when the old row also agrees on these.
IDENTITY_COLUMNS = ("field", "value", "site_name")


def load(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def dump_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def csv_rows(rel: str) -> int:
    with (ROOT / rel).open(encoding="utf-8", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def registry_rows() -> list[dict]:
    match = REGISTRY_RE.search((ROOT / "index.html").read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("index.html: const REGISTRY_DATA = [...]; not found")
    return json.loads(match.group(1))


def mapped(records: list[dict]) -> int:
    return sum(1 for r in records if r.get("lat") is not None and r.get("lon") is not None)


# --------------------------------------------------------------------------- facts


def gather_facts() -> dict[str, Any]:
    rows = registry_rows()
    by_rto: dict[str, int] = {}
    for r in rows:
        by_rto[r["rto"]] = by_rto.get(r["rto"], 0) + 1
    facts: dict[str, Any] = {
        "registry_rows": len(rows),
        "registry_gw": round(sum(float(r["mw"]) for r in rows) / 1000.0, 4),
        "registry_rows_by_rto": by_rto,
        "queues": {},
    }
    for rto, name in QUEUE_SUMMARIES.items():
        if (DATA / name).exists():
            facts["queues"][rto] = load(f"data/{name}")
    projects = load("data/project_level_extractions.json")["records"]
    project_map = load("data/project_level_map.json")["records"]
    aggregates = load("data/supplemental_aggregate_map.json")["records"]
    supplemental = load("data/supplemental_large_load_evidence.json")["records"]
    bpa = load("data/bpa_large_load_registry.json")
    epoch_map = load("data/epoch_ai_map.json")
    targets = load("data/epoch_connection_research_targets.json")
    site_evidence = load("data/epoch_site_evidence_records.json")
    facts.update(
        projects=len(projects),
        project_map=len(project_map),
        project_map_mapped=mapped(project_map),
        aggregates=len(aggregates),
        aggregates_mapped=mapped(aggregates),
        supplemental=len(supplemental),
        bpa=bpa["record_count"],
        bpa_mapped=bpa["mapped_record_count"],
        bpa_unmapped=bpa["unmapped_record_count"],
        epoch_sites=epoch_map["record_count"],
        epoch_sites_mapped=epoch_map.get("mapped_count", mapped(epoch_map["records"])),
        epoch_targets=targets["record_count"],
        epoch_targets_with_evidence=targets.get("summary", {}).get("sites_with_site_evidence"),
        epoch_evidence_items=site_evidence["record_count"],
        epoch_sites_with_evidence=site_evidence.get("sites_with_evidence"),
    )
    return facts


# --------------------------------------------------------------------------- rules


class Drift:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def set(self, obj: dict, key: str, value: Any, where: str) -> bool:
        if value is None or obj.get(key) == value:
            return False
        self.messages.append(f"{where}.{key}: {obj.get(key)!r} -> {value!r}")
        obj[key] = value
        return True


def rule_queue_status(f: dict, d: Drift) -> dict[str, Any]:
    status = load("data/queue_layer_status.json")
    for feed in status["feeds"]:
        s = f["queues"].get(feed["id"])
        if not s:
            continue
        where = f"queue_layer_status[{feed['id']}]"
        d.set(feed, "snapshot_present", True, where)
        d.set(feed, "last_capture", s.get("captured_at"), where)
        d.set(feed, "record_count", s.get("record_count"), where)
        d.set(feed, "records_ge_100mw", s.get("records_ge_100mw"), where)
        d.set(feed, "unresolved_ge_100_location", s.get("missing_ge_100_location"), where)
    captures = [str(x.get("last_capture"))[:10] for x in status["feeds"] if x.get("last_capture")]
    d.set(status, "generated_on", max(captures) if captures else None, "queue_layer_status")
    return {"data/queue_layer_status.json": status}


def _layer_values(f: dict) -> dict[str, dict[str, Any]]:
    values = {
        "CORE_REGISTRY": {"records": f["registry_rows"], "mapped_records": f["registry_rows"]},
        "PROJECT_LEVEL": {"records": f["project_map"], "mapped_records": f["project_map_mapped"]},
        "SUPPLEMENTAL_AGGREGATES": {"records": f["aggregates"], "mapped_records": f["aggregates_mapped"]},
        "SUPPLEMENTAL_EVIDENCE": {"records": f["supplemental"]},
        "EPOCH_AI": {"records": f["epoch_sites"], "mapped_records": f["epoch_sites_mapped"]},
        "CONNECTION_TARGETS": {"records": f["epoch_targets"], "mapped_records": f["epoch_targets"]},
        "BPA_LARGE_LOAD": {"records": f["bpa"], "mapped_records": f["bpa_mapped"]},
    }
    for layer_id, rto in QUEUE_LAYERS.items():
        s = f["queues"].get(rto)
        if s:
            values[layer_id] = {"records": s.get("record_count"), "records_ge_100mw": s.get("records_ge_100mw"),
                                "unresolved_ge_100_location": s.get("missing_ge_100_location")}
    return values


def rule_map_manifest(f: dict, d: Drift) -> dict[str, Any]:
    manifest = load("data/map_layer_manifest.json")
    values = _layer_values(f)
    for layer in manifest["layers"]:
        for key, value in values.get(layer["id"], {}).items():
            d.set(layer, key, value, f"map_layer_manifest[{layer['id']}]")
    # The CSV is a flat export of the JSON layers with a fixed column set.
    columns, existing = read_csv("data/map_layer_manifest.csv")
    return {"data/map_layer_manifest.json": manifest,
            "data/map_layer_manifest.csv": export_csv_text(manifest["layers"], columns, existing)}


def rule_scope(f: dict, d: Drift) -> dict[str, Any]:
    scope = load("data/large_load_scope.json")
    defs = scope["definitions"]
    where = "large_load_scope"
    d.set(defs["current_row_level"], "records", f["registry_rows"], where + ".current_row_level")
    d.set(defs["current_row_level"], "capacity_gw", f["registry_gw"], where + ".current_row_level")
    extra = defs["additional_known_miso"]
    expanded = defs["expanded_known_scope"]
    d.set(expanded, "records", f["registry_rows"] + extra["records"], where + ".expanded_known_scope")
    d.set(expanded, "capacity_gw", round(f["registry_gw"] + float(extra["capacity_gw"]), 4), where + ".expanded_known_scope")
    d.set(expanded, "arithmetic",
          f"{f['registry_rows']} current rows + {extra['records']} MISO records captured {extra.get('capture_date')}; "
          f"{f['registry_gw']} + {extra['capacity_gw']} GW", where + ".expanded_known_scope")
    simple = {
        "project_level_extractions": {"records": f["projects"]},
        "project_level_map": {"records": f["project_map"], "mapped_records": f["project_map_mapped"]},
        "supplemental_evidence_units": {"records": f["supplemental"]},
        "supplemental_aggregate_map": {"records": f["aggregates"], "mapped_records": f["aggregates_mapped"]},
        "epoch_ai_frontier_site_map": {"records": f["epoch_sites"], "mapped_records": f["epoch_sites_mapped"]},
        "epoch_connection_research_targets": {"records": f["epoch_targets"],
                                              "sites_with_site_level_evidence": f["epoch_targets_with_evidence"],
                                              "evidence_items": f["epoch_evidence_items"]},
        "epoch_site_evidence_inventory": {"records": f["epoch_evidence_items"],
                                          "sites_with_evidence": f["epoch_sites_with_evidence"]},
    }
    queue_defs = {"caiso_full_public_queue_report": "CAISO", "miso_current_complete_queue": "MISO",
                  "spp_current_active_queue": "SPP"}
    for key, rto in queue_defs.items():
        s = f["queues"].get(rto)
        if s and key in defs:
            count_key = "report_rows" if key.startswith("caiso") else "records"
            simple[key] = {count_key: s.get("record_count"), "records_ge_100mw": s.get("records_ge_100mw"),
                           "capture_date": str(s.get("captured_at", ""))[:10] or None}
            if rto == "MISO":
                simple[key]["unresolved_ge_100_location"] = s.get("missing_ge_100_location")
    for key, values in simple.items():
        if key in defs:
            for k, v in values.items():
                d.set(defs[key], k, v, f"{where}.{key}")
    return {"data/large_load_scope.json": scope}


def rule_market_manifest(f: dict, d: Drift) -> dict[str, Any]:
    manifest = load("data/market_universe_manifest.json")
    for market in manifest["markets"]:
        rto = next((k for k, v in MARKET_IDS.items() if v == market["id"]), market["id"])
        if rto in f["registry_rows_by_rto"]:
            d.set(market, "core_rows", f["registry_rows_by_rto"][rto], f"market_universe_manifest[{market['id']}]")
        s = f["queues"].get(rto)
        if s and market.get("row_level_snapshot"):
            d.set(market, "complete_queue_rows", s.get("record_count"), f"market_universe_manifest[{market['id']}]")
    g = manifest["global_layers"]
    for key, values in {
        "project_level_extractions": {"records": f["projects"], "mapped_records": f["project_map_mapped"]},
        "supplemental_evidence_units": {"records": f["supplemental"]},
        "supplemental_aggregate_map": {"records": f["aggregates"], "mapped_records": f["aggregates_mapped"]},
        "epoch_ai_frontier_site_map": {"records": f["epoch_sites"], "mapped_records": f["epoch_sites_mapped"]},
    }.items():
        if key in g:
            for k, v in values.items():
                d.set(g[key], k, v, f"market_universe_manifest.global_layers.{key}")
    return {"data/market_universe_manifest.json": manifest}


def _file_count(rel: str) -> int | None:
    """Record count of a catalogued file, using the file's own declared semantics."""
    path = ROOT / rel
    if not path.exists() or path.suffix not in {".json", ".csv"}:
        return None
    if path.suffix == ".csv":
        return csv_rows(rel)
    obj = load(rel)
    if isinstance(obj, list):
        return len(obj)
    special: dict[str, Callable[[dict], int | None]] = {
        "data/company_operator_universe_2026-09-27.json": lambda o: o.get("unique_facility_key_count"),
        "data/company_operator_universe_status.json": lambda o: o.get("operator_count"),
        "data/global_ai_datacenter_coverage_2026-09-27.json": lambda o: len(o.get("candidate_records", [])),
        "data/large_load_scope.json": lambda o: o["definitions"]["expanded_known_scope"]["records"],
        "data/nyiso_public_queue_status.json": lambda o: o.get("record_count", 0),
        "data/physical_verification_layer.json": lambda o: len(o.get("site_records", [])),
        "data/track3/publisher_field_completeness_2026-09-27.json":
            lambda o: sum(len(r.get("field_matrix", {})) for r in o["records"]),
    }
    if rel in special:
        return special[rel](obj)
    if isinstance(obj.get("record_count"), int):
        return obj["record_count"]
    for key in ("records", "claims", "sources", "markets", "rows", "tasks", "cases", "candidates"):
        if isinstance(obj.get(key), list):
            return len(obj[key])
    return None


def rule_catalog(f: dict, d: Drift) -> dict[str, Any]:
    catalog = load("data/public_data_catalog.json")
    for entry in catalog["datasets"]:
        where = f"public_data_catalog[{entry['path']}]"
        count = None if entry["path"] in STATIC_CATALOG_COUNTS else _file_count(entry["path"])
        if count is not None:
            d.set(entry, "record_count", count, where)
        if entry["path"] == "data/large_load_scope.json":
            scope = load("data/large_load_scope.json")["definitions"]
            d.set(entry, "core_record_count", f["registry_rows"], where)
            d.set(entry, "expanded_known_record_count", scope["expanded_known_scope"]["records"], where)
            d.set(entry, "expanded_known_capacity_gw", scope["expanded_known_scope"]["capacity_gw"], where)
        if entry["path"].startswith("data/bpa_large_load_registry."):
            d.set(entry, "mapped_record_count", f["bpa_mapped"], where)
            d.set(entry, "unmapped_record_count", f["bpa_unmapped"], where)
        if "map_count" in entry and entry["path"].endswith(".json"):
            # Only files that declare their own mapped count; others are mapped through a companion layer.
            d.set(entry, "map_count", load(entry["path"]).get("mapped_count"), where)
    return {"data/public_data_catalog.json": catalog}


_MISSING = object()


def _cell(record: dict, column: str, json_lists: bool, previous: dict[str, str] | None) -> str:
    if column.endswith("_json") and column not in record:
        base = column[: -len("_json")]
        if base not in record:
            return (previous or {}).get(column, "")
        value = record[base]
        return "" if value is None else json.dumps(value, ensure_ascii=False)
    value = record.get(column, _MISSING)
    if value is _MISSING:
        # The ledger does not carry this export column: keep the last exported value.
        return (previous or {}).get(column, "")
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        if json_lists:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        return " | ".join("" if v is None else str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def export_csv_text(records: list[dict], columns: list[str], existing: list[dict[str, str]] | None = None) -> str:
    """Flat CSV export that follows the existing file's conventions."""
    existing = existing or []
    json_lists = {c: any((row.get(c) or "").startswith("[") for row in existing) for c in columns}
    key = next((k for k in KEY_COLUMNS if k in columns and any(k in r for r in records)), None)
    previous = {row.get(key): row for row in existing} if key else {}
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(columns)
    identity = [c for c in IDENTITY_COLUMNS if c in columns]
    for record in records:
        prev = previous.get(str(record.get(key))) if key else None
        if prev is not None and any(_cell(record, c, json_lists[c], None) != (prev.get(c) or "")
                                    for c in identity if c in record):
            prev = None  # same key, different record: never borrow its values
        writer.writerow([_cell(record, c, json_lists[c], prev) for c in columns])
    return buf.getvalue()


def read_csv(rel: str) -> tuple[list[str], list[dict[str, str]]]:
    with (ROOT / rel).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def rule_csv_exports(f: dict, d: Drift) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for csv_rel, (json_rel, key) in CSV_EXPORTS.items():
        columns, existing = read_csv(csv_rel)
        records = load(json_rel)[key]
        text = export_csv_text(records, columns, existing)
        current = (ROOT / csv_rel).read_text(encoding="utf-8")
        if _csv_content(current) != _csv_content(text):
            d.messages.append(f"{csv_rel}: CSV export differs from {json_rel} ({csv_rows(csv_rel)} rows vs {len(records)} records)")
            out[csv_rel] = text
    return out


def _csv_content(text: str) -> list[list[str]]:
    """Cell values only, so quoting style alone never counts as drift."""
    return list(csv.reader(io.StringIO(text)))


# CSV exports first so the catalog counts the regenerated files.
RULES = [rule_csv_exports, rule_queue_status, rule_scope, rule_map_manifest, rule_market_manifest, rule_catalog]


def run_pass(check: bool) -> list[str]:
    drift = Drift()
    for rule in RULES:
        facts = gather_facts()  # re-read: earlier rules may have changed an owner (e.g. the scope)
        before = len(drift.messages)
        updates = rule(facts, drift)
        if check or len(drift.messages) == before:
            continue
        for rel, obj in updates.items():
            text = obj if isinstance(obj, str) else dump_json(obj)
            path = ROOT / rel
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                path.write_text(text, encoding="utf-8")
    return drift.messages


def run(check: bool) -> list[str]:
    if check:
        return run_pass(check=True)
    messages: list[str] = []
    for _ in range(5):  # owners and copies form a short DAG; this converges in two or three passes
        changed = run_pass(check=False)
        if not changed:
            return messages
        messages.extend(changed)
    raise SystemExit("refresh_derived_counts: did not converge after 5 passes")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report drift and exit 1 without writing")
    args = ap.parse_args()
    messages = run(check=args.check)
    for msg in messages:
        print(("DRIFT: " if args.check else "UPDATED: ") + msg)
    if args.check:
        print("PASS: every derived count matches its owning file." if not messages else f"FAIL: {len(messages)} drifted copies.")
        return 1 if messages else 0
    print(f"refreshed {len(messages)} derived values" if messages else "derived counts already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
