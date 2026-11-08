#!/usr/bin/env python3
"""Release-consistency checks for the public Track 3 engineering snapshot.

Two kinds of check:

* Claim guards -- statuses that must not be silently upgraded (empirical
  Track 3 verification stays NOT_CLOSED, the one unresolved physical target is
  not promoted, site-level interval telemetry stays empty, ...).
* Reconciliation -- every count that appears in more than one ledger, or in
  the prose docs, must equal the ledger that owns it. No count is hard-coded.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def doc(name: str) -> tuple[str, str]:
    for rel in (f"docs/track3/{name}", f"docs/{name}", name):
        if (ROOT / rel).exists():
            return rel, (ROOT / rel).read_text(encoding="utf-8")
    raise SystemExit(f"missing Track 3 document: {name}")


def stated_counts(text: str, phrase: str) -> set[int]:
    """Numbers written immediately before `phrase` (e.g. '2,809 derived remote-sensing observations')."""
    text = re.sub(r"<!--/?count[^>]*-->", "", text)  # auto-updated counters (refresh_derived_counts.py)
    return {int(n.replace(",", "")) for n in re.findall(r"(\d[\d,]*)\s+" + re.escape(phrase), text)}


def main() -> int:
    s = load("data/track3/summary.json")
    g = load("data/track3/completion_gate.json")
    physical = load("data/physical_verification_layer.json")
    strict = load("data/track3/strict_discovery_case_dispositions_2026-09-28.json")
    cases = load("data/track3/ambiguous_case_studies.json")
    handoff = load("data/track3/external_capability_handoff_2026-09-28.json")
    telemetry = load("data/track3/interval_power_telemetry_protocol.json")
    leads = load("data/track3/physical_target_leads.json")
    closure = load("data/track3/engineering_closure_2026-09-28.json")
    enrichment = load("data/track3/public_web_enrichment_2026-09-27.json")
    backlog = load("data/track3/research_backlog_summary.json")
    reference_sites = len(load("data/external/epoch_ai/site_level_connection_evidence.json")["records"])
    blockers = handoff.get("blockers", [])
    remaining = closure.get("remaining_research_and_acquisition", {})
    gate_accounting = g.get("public_evidence_accounting", {})
    rs_count = s.get("remote_sensing_derived_observation_count")

    checks = [
        # reconciliation
        (s.get("epoch_site_count") == reference_sites, "summary site count differs from the frozen reference universe"),
        (s.get("public_web_evidence_record_count") == enrichment.get("record_count") == len(enrichment.get("records", [])),
         "summary public-web evidence count differs from the enrichment ledger"),
        (gate_accounting.get("public_web_evidence_records") == s.get("public_web_evidence_record_count"),
         "completion gate public-web count differs from the summary"),
        (rs_count == physical.get("summary", {}).get("derived_observation_count"),
         "summary remote-sensing count differs from the physical layer"),
        (gate_accounting.get("remote_sensing_derived_observations") == rs_count,
         "completion gate remote-sensing count differs from the summary"),
        (remaining.get("public_publisher_field_tasks_open") == backlog.get("publisher_tasks"),
         "closure publisher-task count differs from the research backlog"),
        (remaining.get("follow_on_observation_tasks") == s.get("observation_task_count"),
         "closure observation-task count differs from the summary"),
        (closure.get("external_capability_blockers", {}).get("count") == len(blockers),
         "closure external-blocker count differs from the handoff ledger"),
        (len(strict.get("cases", [])) == strict.get("summary", {}).get("terminal_disposition_count") > 0,
         "every strict-discovery case must have a terminal disposition"),
        (len(cases.get("cases", [])) > 0, "the ambiguous-case laboratory is empty"),
        # claim guards
        (g.get("empirical_track3_verification", {}).get("status") == "NOT_CLOSED", "empirical Track 3 status must remain NOT_CLOSED"),
        (closure.get("empirical_track3_verification_status") == "NOT_CLOSED", "empirical Track 3 status must remain NOT_CLOSED"),
        (closure.get("repository_engineering_status") == "COMPLETE", "repository engineering closure must be COMPLETE"),
        (closure.get("untracked_gap_count") == 0, "engineering closure must report zero untracked gaps"),
        (bool(blockers) and {x.get("current_state") for x in blockers} == {"BLOCKED_EXTERNAL_CAPABILITY"},
         "every external-capability blocker must stay explicitly BLOCKED_EXTERNAL_CAPABILITY"),
        (telemetry.get("current_state", {}).get("site_level_interval_records") == 0,
         "site-level interval telemetry must stay empty until real records exist"),
        (g.get("current_public_data_boundaries", {}).get("one_reference_site_without_site_specific_public_physical_target")
         == leads.get("targets", [{}])[0].get("epoch_id", "EPOCH-661288625d17662a"),
         "the unresolved physical target changed without updating the leads ledger"),
        (leads.get("targets", [{}])[0].get("canonical_status") == "UNRESOLVED", "unresolved target was promoted"),
        (leads.get("targets", [{}])[0].get("current_canonical_coordinate") is None,
         "the unresolved target must not carry a canonical coordinate"),
    ]
    errors = [msg for ok, msg in checks if not ok]

    # Prose must point at the ledgers it summarizes, and any count it states must be current.
    required_refs = {
        "TRACK3_ONE_PAGE_SUMMARY.md": ["engineering_closure_2026-09-28.json"],
        "TRACK3_COMPLETION_GATE.md": ["external_capability_handoff_2026-09-28.json", "engineering_closure_2026-09-28.json"],
        "TRACK3_COMPLETE_COVERAGE.md": ["interval_power_telemetry_protocol.json"],
    }
    stated = {
        "derived remote-sensing observations": rs_count,
        "open public-source publisher-field research tasks": backlog.get("publisher_tasks"),
        "public-web evidence records": s.get("public_web_evidence_record_count"),
    }
    for name, refs in required_refs.items():
        rel, text = doc(name)
        errors += [f"{rel} no longer references {ref}" for ref in refs if ref not in text]
        for phrase, current in stated.items():
            stale = stated_counts(text, phrase) - {current}
            if stale:
                errors.append(f"{rel} states {sorted(stale)} {phrase}; the ledgers say {current}")

    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1
    print("PASS: Track 3 release consistency checks passed.")
    print(f"PASS: {reference_sites} sites / {s.get('public_web_evidence_record_count')} public-web records / "
          f"{rs_count} remote observations / {len(cases.get('cases', []))} pilot cases / {len(strict.get('cases', []))} strict cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
