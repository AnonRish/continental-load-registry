# Continental Large-Load Interconnection & Telemetry Registry

[![CI](https://github.com/AnonRish/continental-load-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/AnonRish/continental-load-registry/actions/workflows/ci.yml)
[![Daily refresh](https://github.com/AnonRish/continental-load-registry/actions/workflows/refresh.yml/badge.svg)](https://github.com/AnonRish/continental-load-registry/actions/workflows/refresh.yml)

An open, reproducible registry of very large (≥100 MW) electricity-connection requests across North
American grid operators, built to answer one question for AI-compute accounting: **which large new loads
lack a confirmed public operator, and what does the public record say about each?**

It joins public interconnection queues, utility and regulator filings, Epoch AI's frontier data-center
dataset, and public satellite observations into one evidence ledger. Every record keeps its source URL and
capture date, and every count on the site is checked against the file it comes from.

**Live site:** <https://anonrish.github.io/continental-load-registry/> ·
[Track 3 evidence registry](https://anonrish.github.io/continental-load-registry/track3.html) ·
[AI 2040 Plan A bridge](https://anonrish.github.io/continental-load-registry/plan-a.html) ·
[Bulk downloads](https://anonrish.github.io/continental-load-registry/bulk-download.html)

## Check it yourself (about 10 seconds, offline)

```bash
git clone https://github.com/AnonRish/continental-load-registry
cd continental-load-registry
pip install -r requirements.txt
python verify.py
```

`verify.py` runs every offline check in the repository and prints one verdict: the unit and contract tests,
the pipeline self-tests on synthetic fixtures, the Track 3 calculators on their example inputs, and every
reproducibility check (derived counts, CSV exports, physical-provenance hashes, ledger joins). It never
touches the network, and its last check confirms it changed no tracked file. CI runs the same command on
every push, and the daily refresh must pass it before it may commit.

## What is in the registry

| Layer | Size now | Freshness | Where |
|---|---|---|---|
| Core row-level registry (≥100 MW requests) | <!--count:registry_rows-->1,506<!--/count--> rows · <!--count:registry_gw-->353.7<!--/count--> GW · <!--count:registry_rtos-->9<!--/count--> markets | PJM and ERCOT re-ingested daily; MISO, CAISO, NYISO, ISO-NE, AESO from the 2026-09-19 capture; SPP and IESO from the September 2026 build | `index.html` (embedded), `data/facility_records/` |
| Broader known scope (core + MISO requests whose public record omits location) | <!--count:expanded_rows-->1,589<!--/count--> records · <!--count:expanded_gw-->389.6<!--/count--> GW | the 83 extra MISO records are from 2026-09-19 | `data/large_load_scope.json` |
| Complete public queues (non-additive context) | MISO <!--count:miso_queue_rows-->4,090<!--/count-->, SPP <!--count:spp_queue_rows-->3,079<!--/count-->, CAISO <!--count:caiso_queue_rows-->2,278<!--/count-->, PJM cycle <!--count:pjm_queue_rows-->9,263<!--/count--> | daily | `data/*_public_queue.json` |
| BPA large-load requests | <!--count:bpa_records-->132<!--/count--> | daily | `data/bpa_large_load_registry.json` |
| Project-level utility/regulator records | <!--count:project_records-->271<!--/count--> | curated | `data/project_level_extractions.json` |
| Epoch AI frontier reference universe | <!--count:epoch_sites-->93<!--/count--> sites | frozen; upstream changes are reported in `data/external/epoch_ai/upstream_delta.json` | `data/external/epoch_ai/` |
| Track 3 evidence ledger | <!--count:track3_evidence_records-->3,868<!--/count--> records | rebuilt daily | `data/track3/evidence_records.json` |
| Public satellite observations (Sentinel-1/2, Landsat) | <!--count:remote_sensing_observations-->3,222<!--/count--> across <!--count:remote_sensing_sites-->92<!--/count--> sites | weekly | `data/track3/remote_sensing_observations.json` |

The figures above are maintained by `scripts/refresh_derived_counts.py`, so they always match the data.
Of the core rows, <!--count:registry_storage_rows-->1,364<!--/count--> are confirmed grid-scale battery storage and
<!--count:registry_ambiguous_rows-->142<!--/count--> carry no storage signal. "Ambiguous" means unresolved from public
queue data alone. It is never a finding that a load is AI compute.

## How the numbers stay honest

- **Every copied number has one owner.** The registry row count lives in `index.html`, the MISO queue size
  in `data/miso_public_queue_summary.json`, and so on. Manifests, the data catalog, CSV exports and the
  prose figures in this README and the docs are rewritten from those owners
  (`python scripts/refresh_derived_counts.py`), and `--check` fails CI if any copy drifts.
- **Provenance describes the right bytes.** Each facility record cites the capture its row was built from.
  The daily complete-queue snapshots are recorded separately (`latest_public_snapshot` in
  `data/source_manifest.json`), so a frozen 2026-09-19 row never claims a newer capture.
- **Estimates only where they mean something.** GPU and FLOP figures are hypothetical ("if this capacity
  were AI compute") and are never attached to battery storage.
- **Claims that may not be silently upgraded are tested.** For example, empirical Track 3 verification
  stays `NOT_CLOSED`, and the one unresolved physical target cannot be promoted without new evidence
  (`scripts/validate_track3_release.py`).

## Automation

| Workflow | When | What it does |
|---|---|---|
| [`ci.yml`](.github/workflows/ci.yml) | every push and pull request | `python verify.py`, a stylesheet freshness check, workflow lint. Never commits. |
| [`refresh.yml`](.github/workflows/refresh.yml) | daily 06:17 UTC, or manually | Refreshes every public source in sequence (registry, BPA, queues, Epoch, compute universes, Track 3), rebuilds derived counts, runs `verify.py`, then makes **one** commit. A failing source skips only its own steps and is listed in the run summary. |
| weekly physical jobs | Sundays | Satellite scenes and building footprints (`requirements-physical.txt`). |

Run one source by hand, for example:

```bash
python scripts/ingest_grid_queues.py --include-raw-fields --output /tmp/registry_raw.csv   # PJM + ERCOT
python scripts/sync_miso_public_queue.py --help
python scripts/refresh_derived_counts.py            # then commit the refreshed copies
```

Third-party aggregators (Compute Atlas, Data Center Index) are fetched only where their `robots.txt`
allows it (`scripts/polite_fetch.py`); otherwise the site links to the publisher's own data page.

## AI 2040 Plan A / Track 3

This is an independent public-data contribution to the Track 3 problem (finding undeclared compute)
in the AI Futures Project's AI 2040 Plan A. It provides a source-backed evidence layer, a research queue,
a public physical-observation pipeline and a machine-readable mapping to Plan A's recommendations
(`data/track3/ai2040_plan_a_mapping.json`). It is **not** an AI Futures Project publication, a formal
Track 3 implementation, or proof that covert facilities exist or do not. A project that avoids new
publicly visible interconnection, permits or construction can evade every signal used here.

Start with [`docs/PLAN_A.md`](docs/PLAN_A.md), [`docs/TRACK3.md`](docs/TRACK3.md),
[`docs/TRACK3_ONE_PAGE_SUMMARY.md`](docs/TRACK3_ONE_PAGE_SUMMARY.md) and the
[closed-case pilot](https://anonrish.github.io/continental-load-registry/closed-cases.html). Open
research is tracked, not hidden: <!--count:publisher_tasks-->214<!--/count--> publisher-field tasks and
<!--count:observation_tasks-->24<!--/count--> follow-on observation tasks (`data/track3/research_work_queue.json`).
The companion repository [`AnonRish/ai-2040-verification`](https://github.com/AnonRish/ai-2040-verification)
tests inference-side verification mechanisms at a different evidence layer.

## Regulatory filings

The registry supports two public filings by the Computational Infrastructure & Grid Telemetry Initiative:

- comments to FERC in Docket No. RM26-4-000 on telemetry for large computational loads
  ([PDF](FERC_Docket_RM26-4-000_Comments_Computational_Load_Telemetry.pdf));
- a petition for rulemaking to BIS under 5 U.S.C. § 553(e) proposing a CEII-protected telemetry-sharing
  protocol ([PDF](BIS_Rulemaking_Petition_5USC553e_Computational_Load_CEII_Protocol.pdf)).

## Known limitations

- MISO, CAISO, NYISO, ISO-NE, AESO, SPP and IESO rows in the core registry are frozen captures. Their
  complete public queues refresh daily but are kept separate, because a generator queue row is not a
  large-load request.
- IESO's application-status page renders its grid in the browser, so the automated capture is recorded as
  `PARSE_BLOCKED` (zero rows means not parsed, not no applications).
- NYISO's workbook was unavailable at the latest capture, so no NYISO complete-queue snapshot is published.
- Public absence is never treated as evidence of absence.

## Repository layout

```
index.html, *.html     the public site (GitHub Pages serves the repository root)
assets/                static Tailwind build for index.html
data/                  every published dataset (see data/public_data_catalog.json)
scripts/               ingest, sync, build and validation scripts
tests/, track3/        pytest suites
docs/                  methodology and Track 3 documentation (docs/archive/: dated snapshots)
verify.py              the offline verification entry point
```

## Contributing, citation, license

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CITATION.md`](CITATION.md) (also `CITATION.cff`).
Apache License 2.0, see [`LICENSE`](LICENSE). Contact: grid.telemetry.initiative@gmail.com
