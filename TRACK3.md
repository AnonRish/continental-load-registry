# Track 3 Evidence Layer

This layer turns the continental registry from a queue table into an auditable evidence graph for whether material AI compute can be accounted for through public physical, electrical, hardware, and independent evidence.

## Evidence states

**PENDING_RESEARCH**, **SOURCE_AVAILABLE_NOT_INGESTED**, and **NOT_INGESTED** never mean that a facility or compute stockpile is absent.

| State | Meaning |
|---|---|
| VERIFIED_SITE_SPECIFIC | A defensible site-specific queue/connection record is attached. |
| SITE_LEVEL_EVIDENCE | A site-specific utility, service, planning, regulatory, or facility record exists, but no queue ID is asserted. |
| JURISDICTION_ONLY | The applicable grid/connection family is known, but the physical site is not tied to a site-specific public record. |
| PENDING_RESEARCH | The site-specific search has not yet produced a retained connection/service record. |
| SOURCE_AVAILABLE_NOT_INGESTED | A relevant public external dataset exists and is cataloged, but has not yet been joined to the evidence graph. |
| NOT_INGESTED | The evidence stream is specified by the verification design but numeric observations are not yet ingested. |
| UNKNOWN | The evidence needed to classify the field is not currently available. |

## Current site evidence

As of 2026-09-26, the preserved 93-site Epoch universe has 35 sites with at least one attached site-level evidence item and 58 without one. Two have site-specific queue IDs in the current crosswalk.

The pending research queue is deliberately retained as a worklist. The absence of a public record after a particular search is not treated as proof of absence.

## Evidence domains

Each Epoch site receives machine-readable status for site identity, construction history, chip inventory, grid/connection, actual power telemetry, remote sensing, cooling, transformer supply chain, chip ownership, chip users, and chip shipments.

## Build

```
python build_track3_evidence.py
```

Outputs:

- `data/track3/site_status.json`
- `data/track3/evidence_records.json`
- `data/track3/research_queue.json`
- `data/track3/summary.json`

The Epoch sync workflow rebuilds and validates these artifacts after refresh.

## Measurement separation

Epoch IT power, projected IT power, utility service capacity, queue/interconnection capacity, transmission capacity, generation capacity, contracted demand, chip TDP, and actual measured site load are different measurements and must remain separate.
