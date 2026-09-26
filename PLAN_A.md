# AI 2040 Plan A — Track 3 Research Contribution

## Purpose

This repository is an independent open-source research and data-engineering contribution intended to make public evidence relevant to AI 2040 Plan A Track 3 easier to find, audit, reproduce, and extend.

AI 2040 describes Track 3 as **“Verifying the absence of secret compute.”** Its Plan A covert-projects supplement focuses on accounting for pre-deal AI-relevant compute, tracing sales and resales to physical end use, and locating remaining unaccounted compute with external evidence such as aerial imagery and incentive programs.

**This repository is not an AI Futures Project publication, does not speak for AI 2040, and does not certify compliance with any treaty or verification regime.** The mapping below documents where this repository can contribute data, schemas, source collection, and reproducible research.

## Primary AI 2040 references

- Track 3: https://ai-2040.com/supplements/verification-plan/get-involved
- Plan A — Covert AI Projects: https://ai-2040.com/print/covert-ai-projects
- Plan A scenario: https://ai-2040.com/print/scenario?book=1&plan=A

## What this repository contributes today

### Physical and grid evidence

The repository maintains a nine-market North American large-load registry and a separate Epoch AI frontier-data-center evidence layer. It preserves site identity, construction history, grid/connection evidence, service/contract evidence, power observations, cooling observations, and research backlogs.

The central rule is that queue/interconnection capacity, utility service capacity, Epoch IT power, projected IT power, contracted demand, chip TDP, and measured site load are different quantities. The pipeline does not silently substitute one for another.

### Global compute-accounting source snapshots

The Track 3 sync preserves public Epoch AI source snapshots covering chip ownership, chip users, chip sales, GPU clusters, chip components, and cooling datasets where the source is available. These are retained as source evidence and are **not** automatically assigned to a specific site.

### Provenance

The public data model retains source URLs, capture dates where available, raw source values, normalized values, evidence scope, status, and hashes for preserved source snapshots. Missing or inaccessible evidence is represented explicitly rather than interpreted as proof of absence.

## Direct mapping to the AI 2040 Plan A Track 3 work

The machine-readable mapping is:

`data/track3/ai2040_plan_a_mapping.json`

It distinguishes:

- `INGESTED_SNAPSHOT` — a source snapshot is actually preserved.
- `PARTIAL` — part of the requirement is represented, but the complete verification chain is not.
- `DESIGN_ONLY` — the data model or research pathway is documented, but no completed public result is claimed.

The highest-value future contributions are the parts AI 2040 discusses that cannot be closed by a datacenter queue alone: complete semiconductor production accounting; transaction-level sales and resales; recursive ownership tracing; physical inspection; serial-number continuity; verified decommissioning/recycling; randomized sampling of smaller owners; and a measured untraced pool.

## What a useful contribution looks like

A contribution should add one or more **specific evidence objects**, not just a narrative claim. The preferred unit is:

`entity/site/batch -> source -> raw observation -> normalized value -> provenance -> review state`

For a new record, preserve the original publisher value exactly when possible, then store the normalized value separately. Include the observed date, capture date, official source URL, and enough context for another researcher to reproduce the finding.

Do not turn:

- a state-level queue jurisdiction into a site-specific queue ID;
- an annual electricity total into interval telemetry;
- an estimated chip quantity into a physical inspection;
- a company identity inference into a verified ownership relationship;
- a missing public record into a conclusion that the underlying asset does not exist.

## Research priority

The current public pipeline is strongest where public evidence exists for large physical facilities and grid relationships. The remaining gaps should be closed in a way that progressively connects:

`production -> sale -> transfer/resale -> current owner -> physical location -> inspection`

and separately:

`unrecorded / unresolved -> external discovery -> candidate site -> physical evidence -> verified accounting`

That is the core bridge from a public infrastructure registry to the broader Track 3 accounting problem.

## Citation

For a compact machine-readable citation, use `CITATION.cff`.

When describing the work, a neutral formulation is:

> AnonRish, *Continental Large-Load Interconnection & Telemetry Registry: AI 2040 Plan A Track 3 research contribution*, 2026, https://github.com/AnonRish/continental-load-registry

Please cite the specific upstream publisher or dataset alongside this repository when a claim depends on it.
