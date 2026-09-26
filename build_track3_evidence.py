#!/usr/bin/env python3
"""
Build Track 3 evidence artifacts from the preserved Epoch site universe and
site-level research layer.

The builder never interprets a missing record as evidence of absence.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
EPOCH = ROOT / "data" / "external" / "epoch_ai"
OUT = ROOT / "data" / "track3"

SOURCE_STACK = ROOT / "data" / "track3_source_stack.json"
EVIDENCE = EPOCH / "site_level_connection_evidence.json"
REGISTRY = EPOCH / "registry.json"
GAP = EPOCH / "queue_gap_analysis.csv"

SITE_DOMAINS = (
    "site_identity",
    "construction",
    "chip_inventory",
    "grid_connection",
    "power_telemetry",
    "remote_sensing",
    "cooling",
    "transformer_supply_chain",
    "chip_ownership",
    "chip_users",
    "chip_shipments",
)

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

EXTERNAL_SOURCE_FILES = {
    "chip_ownership": [
        "ai_chip_owners_cumulative_by_designer.csv",
        "ai_chip_owners_quarters_by_chip_type.csv",
        "ai_chip_owners_cumulative_by_chip_type.csv",
    ],
    "chip_users": [
        "ai_chip_users_year_end_by_lab.csv",
        "ai_chip_users_intermediates_by_lab.csv",
    ],
    "chip_shipments": [
        "ai_chip_sales_chip_types.csv",
        "ai_chip_sales_organizations.csv",
        "ai_chip_sales_timelines_by_chip.csv",
    ],
    "cooling": [
        "data_center_chillers.csv",
        "data_center_cooling_towers.csv",
    ],
}

def external_snapshot_available(domain: str) -> bool:
    return all((EPOCH / name).exists() and (EPOCH / name).stat().st_size > 0
               for name in EXTERNAL_SOURCE_FILES[domain])

def site_status(rec: dict[str, Any], domain: str) -> dict[str, Any]:
    ev = rec.get("site_level_connection_evidence") or []
    grid = rec.get("grid_crosswalk") or {}
    crosswalk_ev = grid.get("site_level_public_evidence") or {}
    crosswalk_status = str(crosswalk_ev.get("status") or "").lower()
    if domain == "site_identity":
        return {
            "status": "INGESTED",
            "basis": "Epoch AI site record imported."
        }
    if domain == "construction":
        return {
            "status": "INGESTED" if rec.get("timeline_record_count", 0) > 0 else "UNKNOWN",
            "basis": "Epoch AI dated timeline records are retained."
            if rec.get("timeline_record_count", 0) > 0 else "No retained Epoch timeline rows."
        }
    if domain == "chip_inventory":
        return {
            "status": "INGESTED" if rec.get("chip_quantity_record_count", 0) > 0 else "UNKNOWN",
            "basis": "Epoch AI site-level chip-quantity records are retained."
            if rec.get("chip_quantity_record_count", 0) > 0 else "No retained site-level chip-quantity rows."
        }
    if domain == "grid_connection":
        connection_types = {"site_specific_queue", "site_specific_utility_relationship", "site_specific_utility", "site_specific_service", "site_specific_service_contract", "site_specific_power_request", "site_specific_load_request"}
        connection_evidence = [x for x in ev if x.get("type") in connection_types]
        crosswalk_connection_evidence = bool(
            crosswalk_ev and (
                "grid_record" in crosswalk_status
                or "utility_record" in crosswalk_status
                or "service_record" in crosswalk_status
                or "regulatory_record" in crosswalk_status
                or "power_request" in crosswalk_status
                or "load_request" in crosswalk_status
            )
        )
        if grid.get("site_specific_queue_id"):
            return {
                "status": "VERIFIED_SITE_SPECIFIC",
                "basis": "A site-specific queue/connection ID is present in the preserved crosswalk."
            }
        if any(x.get("type") == "site_specific_queue" for x in connection_evidence):
            return {
                "status": "VERIFIED_SITE_SPECIFIC",
                "basis": "Site-level queue evidence is attached to the Epoch record."
            }
        if connection_evidence or crosswalk_connection_evidence:
            return {
                "status": "SITE_LEVEL_EVIDENCE",
                "basis": "At least one site-level utility, service, power-request, load-request, regulatory, or public grid record is attached; no queue ID is asserted."
            }
        return {
            "status": "PENDING_RESEARCH",
            "basis": "No site-level connection/service evidence is currently attached."
        }
    if domain in {"power_telemetry", "remote_sensing", "cooling", "transformer_supply_chain"}:
        return {
            "status": "NOT_INGESTED",
            "basis": "The public repository currently specifies this evidence stream but does not ingest its measurements."
        }
    if domain in {"chip_ownership", "chip_users", "chip_shipments"}:
        if external_snapshot_available(domain):
            return {
                "status": "INGESTED_SNAPSHOT",
                "basis": "The corresponding Epoch global compute-accounting source is preserved as a raw snapshot; it is not attributed to this site unless a separate site-level linkage exists."
            }
        return {
            "status": "SOURCE_AVAILABLE_NOT_INGESTED",
            "basis": "The relevant Epoch global compute-accounting source is cataloged, but its raw snapshot is not present in this build."
        }
    raise KeyError(domain)

def evidence_domain(ev: dict[str, Any]) -> str:
    t = str(ev.get("type") or "")
    if t == "site_specific_regulatory" or "regulatory" in t:
        return "regulatory"
    if t in {"site_specific_service_contract", "site_specific_service", "site_specific_utility_relationship", "site_specific_utility", "site_specific_power_request", "site_specific_load_request", "site_specific_queue"}:
        return "grid_connection"
    if t in {"site_specific_facility_record", "site_specific_project_record"}:
        return "site_identity"
    if t == "site_specific_utility_planning":
        return "service_or_contract"
    return "grid_connection"

def build_evidence_index(evidence: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    registry_by_id = {x["epoch_id"]: x for x in registry["records"]}
    for rec in evidence["records"]:
        for idx, ev in enumerate(rec.get("site_level_evidence") or [], start=1):
            raw = {
                "epoch_id": rec["epoch_id"],
                "epoch_name": rec.get("epoch_name"),
                "evidence_index": idx,
                "evidence": ev,
            }
            eid = "EVID-" + hashlib.sha256(
                json.dumps(raw, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()[:20]
            item = {
                "evidence_id": eid,
                "target_type": "epoch_site",
                "target_id": rec["epoch_id"],
                "target_name": rec.get("epoch_name"),
                "domain": evidence_domain(ev),
                "evidence_type": ev.get("type"),
                "claim_scope": "site_level",
                "status": "VERIFIED_SITE_SPECIFIC" if ev.get("type") == "site_specific_queue" else "SITE_LEVEL_EVIDENCE",
                "source_kind": ev.get("source_kind"),
                "source_name": ev.get("authority"),
                "source_url": ev.get("source_url"),
                "observed_on": None,
                "captured_on": evidence.get("generated_on"),
                "confidence": ev.get("confidence"),
                "basis": ev.get("basis"),
                "record_id": ev.get("record_id"),
                "authority": ev.get("authority"),
                "capacity_mw": ev.get("capacity_mw"),
                "site_specific": bool(ev.get("type") == "site_specific_queue"),
                "independent_of_other_source": None,
                "review_state": "PUBLISHED_RECORD",
            }
            rows.append(item)

    # Preserve the public grid/facility evidence embedded in the queue
    # crosswalk as its own provenance layer. These values are source-specific
    # and are never silently promoted to a queue ID or measured load.
    for rec in registry["records"]:
        grid = rec.get("grid_crosswalk") or {}
        ev = grid.get("site_level_public_evidence")
        if not ev:
            continue
        raw = {
            "epoch_id": rec["epoch_id"],
            "source": ev.get("source"),
            "url": ev.get("url"),
            "status": ev.get("status"),
        }
        eid = "EVID-XW-" + rec["epoch_id"]
        status = str(ev.get("status") or "").lower()
        domain = "grid_connection" if any(
            token in status for token in ("grid_record", "utility_record", "service_record", "regulatory_record", "power_request", "load_request")
        ) else "site_identity"
        rows.append({
            "evidence_id": eid,
            "target_type": "epoch_site",
            "target_id": rec["epoch_id"],
            "target_name": rec.get("normalized", {}).get("name"),
            "domain": domain,
            "evidence_type": ev.get("status"),
            "claim_scope": "site_level",
            "status": "SITE_LEVEL_EVIDENCE",
            "source_kind": "queue crosswalk public evidence",
            "source_name": ev.get("source") or ev.get("authority"),
            "source_url": ev.get("url"),
            "observed_on": None,
            "captured_on": grid.get("source_date") or evidence.get("generated_on"),
            "confidence": None,
            "basis": ev.get("basis"),
            "record_id": ev.get("record_id"),
            "authority": ev.get("grid_operator") or ev.get("authority"),
            "capacity_mw": None,
            "site_specific": False,
            "independent_of_other_source": None,
            "review_state": "PUBLISHED_CROSSWALK_EVIDENCE",
        })
    return rows

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    reg = load_json(REGISTRY)
    evidence = load_json(EVIDENCE)
    source_stack = load_json(SOURCE_STACK)
    gaps = list(csv.DictReader(GAP.open("r", encoding="utf-8-sig", newline="")))

    epoch_ids = {str(x["epoch_id"]) for x in reg["records"]}
    evidence_ids = {str(x["epoch_id"]) for x in evidence["records"]}
    if len(epoch_ids) != 93 or epoch_ids != evidence_ids:
        raise SystemExit("Epoch registry and evidence layer must match 1:1 across 93 sites.")
    if len(gaps) != 93:
        raise SystemExit(f"Expected 93 gap-analysis rows, got {len(gaps)}.")

    evidence_by_id = {x["epoch_id"]: x for x in evidence["records"]}
    site_records = []
    status_counts: dict[str, dict[str, int]] = {d: {} for d in SITE_DOMAINS}

    for rec in reg["records"]:
        ev = evidence_by_id[rec["epoch_id"]]
        domains = {}
        for domain in SITE_DOMAINS:
            s = site_status(
                {
                    **rec,
                    "site_level_connection_evidence": ev.get("site_level_evidence") or [],
                    "grid_crosswalk": rec.get("grid_crosswalk") or {},
                },
                domain,
            )
            domains[domain] = s
            status_counts[domain][s["status"]] = status_counts[domain].get(s["status"], 0) + 1

        base_evidence_count = len(ev.get("site_level_evidence") or [])
        crosswalk_evidence_count = 1 if (rec.get("grid_crosswalk") or {}).get("site_level_public_evidence") else 0
        site_records.append({
            "epoch_id": rec["epoch_id"],
            "site_name": rec.get("normalized", {}).get("name"),
            "country": rec.get("normalized", {}).get("country"),
            "state_province": rec.get("normalized", {}).get("region_inferred_from_address"),
            "current_it_power_mw": rec.get("normalized", {}).get("current_power_mw"),
            "current_h100_equivalents": rec.get("normalized", {}).get("current_h100_equivalents"),
            "domains": domains,
            "site_level_evidence_count": base_evidence_count,
            "crosswalk_public_evidence_count": crosswalk_evidence_count,
            "combined_site_level_evidence_count": base_evidence_count + crosswalk_evidence_count,
            "next_action": ev.get("next_action"),
        })

    pending = [x for x in site_records if x["domains"]["grid_connection"]["status"] == "PENDING_RESEARCH"]
    evidence_index = build_evidence_index(evidence, reg)

    summary = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "epoch_site_count": len(site_records),
        "site_level_evidence_site_count": sum(1 for x in site_records if x["site_level_evidence_count"] > 0),
        "combined_site_level_evidence_site_count": sum(
            1 for x in site_records
            if x["combined_site_level_evidence_count"] > 0
        ),
        "site_specific_queue_id_count": sum(1 for x in site_records if x["domains"]["grid_connection"]["status"] == "VERIFIED_SITE_SPECIFIC"),
        "pending_grid_connection_research_count": len(pending),
        "domain_status_counts": status_counts,
        "source_stack_count": len(source_stack.get("sources", [])),
        "source_stack_status_counts": {
            status: sum(1 for source in source_stack.get("sources", []) if source.get("status") == status)
            for status in sorted({source.get("status") for source in source_stack.get("sources", []) if source.get("status")})
        },
        "semantics": "PENDING and NOT_INGESTED are explicit states and are never interpreted as evidence of absence.",
    }

    (OUT / "site_status.json").write_text(json.dumps({
        "schema_version": 1,
        "summary": summary,
        "records": site_records,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (OUT / "evidence_records.json").write_text(json.dumps({
        "schema_version": 1,
        "record_count": len(evidence_index),
        "records": evidence_index,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (OUT / "research_queue.json").write_text(json.dumps({
        "schema_version": 1,
        "count": len(pending),
        "records": pending,
        "semantics": "A pending record means the registry has not attached site-specific grid/service evidence yet; it does not mean the site lacks a connection.",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    external_audit = []
    for domain, filenames in EXTERNAL_SOURCE_FILES.items():
        for filename in filenames:
            path = EPOCH / filename
            row_count = 0
            columns = []
            if path.exists() and path.stat().st_size > 0:
                try:
                    with path.open("r", encoding="utf-8-sig", newline="") as f:
                        reader = csv.reader(f)
                        columns = next(reader, [])
                        row_count = sum(1 for _ in reader)
                except Exception:
                    row_count = -1
            external_audit.append({
                "domain": domain,
                "file": filename,
                "status": "INGESTED_SNAPSHOT" if row_count >= 0 and path.exists() and path.stat().st_size > 0 else "SOURCE_AVAILABLE_NOT_INGESTED",
                "row_count": row_count,
                "columns": columns,
            })
    (OUT / "external_source_snapshots.json").write_text(json.dumps({
        "schema_version": 1,
        "generated_at_utc": summary["generated_at_utc"],
        "records": external_audit,
        "semantics": "These are source snapshots, not site-attributed compute records."
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
