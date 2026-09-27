# Continental Large-Load Interconnection & Telemetry Registry

**Version 2.3** -- adds per-facility research records, an official source catalog,
and automated regeneration of those records during refresh.

Open-source ETL pipeline and public dashboard tracking large (>=100 MW)
bulk-power interconnection requests across nine RTOs/ISOs -- PJM, ERCOT,
SPP, MISO, CAISO, NYISO, and ISO-NE in the U.S., and Canada's IESO and
AESO -- with an entity-resolution and power-to-compute estimation pass
aimed at surfacing large requests that lack a confirmed public operator.

## What's in this repository

- `ingest_grid_queues.py` -- extracts, normalizes, and filters the nine
  source registers into one schema (`queue_id`, `rto_region`, `state`,
  `county`, `poi_substation`, `capacity_mw`, `projected_date`,
  `developer_entity`, plus `status` / `project_name` / `raw_fuel_technology`
  with `--include-raw-fields`). Run `python ingest_grid_queues.py --help`
  for the full flag list, or `--selftest` to run the current 43-check suite
  against synthetic fixtures without hitting any network.
- `compute_anomaly_detector.py` -- entity resolution against a small known
  hyperscaler/colocation-developer list, a PJM-specific heuristic for
  undisclosed developers, and a low/reference/high power-to-compute (FLOPs)
  range estimate. Also has `--selftest`. Unchanged in the MISO/CAISO/NYISO/
  ISO-NE/AESO update: its "Developer Not Disclosed" check already keys on the
  `NOT PUBLISHED...` prefix the new adapters use.
- `embed_registry_data.py` -- refreshes the data embedded in `index.html`
  from the two scripts' CSVs. Only the RTOs present in the CSVs are
  replaced, so one source can be refreshed without re-running the other
  eight, and re-running it is idempotent. `--dry-run` prints the
  before/after row and GW counts without writing.
- `build_facility_records.py` -- turns each published facility into a
  research-record artifact with the full union of normalized fields, retained
  ingest-level source fields when available, source/capture metadata, official
  links, and a source -> raw extract -> normalization -> enrichment ->
  publication provenance trail. `--check` verifies that every published
  facility has exactly one research record.
- `data/source_manifest.json` -- machine-readable official source catalog,
  including publisher, source URL, capture date/precision, scope, and source
  snapshot hashes where a source snapshot was retained by the build.
- `data/facility_records/` -- one JSON record set per RTO plus `index.json`.
  The public dashboard loads the relevant RTO file when a facility's Details
  view is opened.
- `index.html` -- the public dashboard. Single-file, Tailwind (CDN) +
  vanilla JS, no build step. The registry table's data is embedded
  directly in the file (by `embed_registry_data.py`), not fetched at
  page-load. Prose that quotes a count or a GW figure is filled in from
  that data at load time, so a re-embed cannot leave a stale number behind.
- `track3.html` -- the public Track 3 Evidence Observatory. It loads the canonical Track 3 site-status, evidence, observation, power/cooling, source-stack, queue/source-universe, Module 1 gate, and external-source status artifacts, with site search, grid-state filtering, per-site evidence inspection, domain coverage accounting, source links, and explicit missingness semantics.
- `plan-a.html` -- public AI 2040 Plan A Track 3 research bridge. It maps the repository's current evidence and research tasks to the public AI 2040 Track 3 / Covert AI Projects discussion, provides direct AI 2040 reference links, and explains what is implemented, partial, or still design-only.
- `PLAN_A.md` -- the repository-level Plan A contribution notes and scope boundary. This is an independent research contribution, not an AI Futures Project publication or certification.
- `CONTRIBUTING.md` -- evidence-submission protocol for adding reproducible Track 3 records.
- `CITATION.cff` -- machine-readable repository citation metadata.

## AI 2040 Plan A / Track 3 reference surface

For researchers using this repository specifically in the context of AI 2040 Plan A Track 3, start with the public [Plan A / Track 3 research bridge](https://anonrish.github.io/continental-load-registry/plan-a.html), then use the [Track 3 Evidence Observatory](https://anonrish.github.io/continental-load-registry/track3.html) for the underlying site/evidence layer.

The repository separates three things that should not be conflated:

- AI 2040's public proposal and terminology, which should be cited directly from AI 2040.
- Repository-derived observations and generated artifacts, which should be cited by artifact path and commit/version.
- Upstream datasets and source records, which should be cited alongside the repository when they support a factual claim.

Machine-readable Plan A mapping is in `data/track3/ai2040_plan_a_mapping.json`; Recommendation / Appendix B traceability is in `data/track3/ai2040_plan_a_traceability.json`; the audit-chain schema is in `data/track3/plan_a_audit_schema.json`; and the complete commit-level CI audit is in `data/ci/commit_audit.json` with a human-readable companion at `CI_AUDIT_2026-09-26.md`.

The repository is an independent research contribution. It is not an AI Futures Project publication, does not speak for AI 2040, and does not certify a verification regime.

The public research-surface CI is defined in `.github/workflows/validate_public_surface.yml` and separately validates the Plan A / Track 3 pages and machine-readable documentation contracts.


- `.github/workflows/monthly_registry_update.yml` -- refreshes the registry
  from the live feeds on the 1st of every month, 06:00 UTC, or on demand, and
  commits the result to `main`. See "Automated monthly refresh".
- `data/archive/registry_snapshot_2026-09-24.csv` -- preserved 1,802-record
  publication snapshot from September 24, 2026. It is intentionally separate
  from the current registry so superseded queue rows remain auditable without
  being counted as current active facilities.
- `guard_registry_refresh.py` -- (2.1) the per-RTO sanity gate that workflow
  runs between the pipeline and `embed_registry_data.py`. Has `--selftest`.
- `investigate_ambiguous_loads.py` -- (2.1) builds
  `ambiguous_facilities_dossier.md`, a worklist of search leads for the
  ambiguous large loads, and applies human-verified identities from
  `ground_truth_overrides.json`. Has `--selftest`. See "Investigating the
  ambiguous tier".
- `ground_truth_overrides.json` (empty template),
  `ground_truth_overrides.example.json` (a complete, fictional entry) and
  `ambiguous_facilities_dossier.md` (generated from this build's data with
  `--input data/computational_load_estimates_new5.csv`).
- `data/` -- the retained ingest outputs, source manifest, per-RTO research
  records, historical snapshot, and `SOURCES.md`. The publisher's original
  source files are not bundled; where a source snapshot was preserved for the
  build, its SHA-256 is recorded.
- `requirements.txt` (unchanged: the 2.1 scripts use only the standard library), `LICENSE` (Apache 2.0).

## Epoch AI secondary evidence layer

The repository also imports the current Epoch AI AI Data Centers dataset as a
separate research layer. Epoch's public dataset was updated September 24,
2026 and currently covers 93 major AI data-center sites. Epoch describes the
dataset as independent research using satellite imagery, permits, public
documents, company disclosures and regulatory filings. Its public
documentation defines core site fields including current H100-equivalents,
current IT power, owner/user confidence, country, address and selected
sources, with separate timeline and chip-quantity records. See:
https://epoch.ai/data/ai-data-centers
and https://epoch.ai/data/data-centers-documentation/records.

The repository keeps the source-specific values separate:

- data/external/epoch_ai/data_centers.csv -- raw Epoch data-center table.
- data/external/epoch_ai/data_center_timelines.csv -- raw dated timeline records.
- data/external/epoch_ai/data_centers_chip_quantities.csv -- raw chip-quantity records.
- data/external/epoch_ai/registry.json -- 93 normalized Epoch site records, latest available timeline snapshot, latest chip quantities by type, all raw data-center row values, source metadata and crosswalk.
- data/external/epoch_ai/crosswalk.csv -- one row for every Epoch site, showing conservative matches to current queue records.
- data/external/epoch_ai/queue_crosswalk.csv -- one row for every Epoch site with its geographic grid/queue jurisdiction and any site-specific queue/service evidence found.
- data/external/epoch_ai/queue_crosswalk.json -- the same 93-site geographic queue/connection crosswalk in machine-readable JSON.
- data/external/epoch_ai/manifest.json -- capture metadata, row counts and SHA-256 hashes.
- data/external/epoch_ai/match_overrides.json -- human-reviewed queue crosswalk overrides; currently records the Lake Mariner campus/phase relationship to NYISO Q1670.
- build_epoch_grid_crosswalk.py -- rebuilds the 93-site geographic queue/connection crosswalk and embeds it into registry.json.

A complete source-universe catalog is maintained in `QUEUE_REGISTRY_UNIVERSE.md`
and as `data/external/epoch_ai/queue_source_universe.json`. The catalog currently
contains **26 direct queue/connection registries, 14 cross-cutting public
sources, and 4 supporting public-record source families**.

The project also produces:
- `data/external/epoch_ai/queue_crosswalk.csv` -- geographic queue/connection jurisdiction for every Epoch site.
- `data/external/epoch_ai/queue_gap_analysis.csv` -- the 93-site research worklist for closing remaining site-specific queue/connection gaps.
- `data/external/epoch_ai/queue_gap_analysis.json` -- machine-readable version of the same worklist.
`data/track3/` -- canonical Track 3 site-status, evidence-record, research-queue, observation-queue, and summary artifacts.
`data/track3/power_observations.json` -- site-level annual electricity-consumption observations with source provenance; these are not interval meter telemetry.
`data/track3/cooling_observations.json` -- selected site-level cooling-equipment observations with source provenance.
- `build_epoch_grid_crosswalk.py` -- rebuilds the complete jurisdiction layer.
- `build_epoch_queue_gap_analysis.py` -- rebuilds the 93-site gap analysis.
The crosswalk is intentionally conservative. **All 93 Epoch sites now have a
grid/queue or connection-system jurisdiction.** That is different from a
site-specific queue ID. For the 77 U.S. sites, the jurisdiction points to the
applicable RTO/ISO or utility/transmission-provider queue family. For the 16
international sites, the record identifies the relevant national or utility
connection system while keeping them outside the North American queue totals.

A "site-specific queue ID not yet verified" result means the repository has not
established that the Epoch campus is a particular row in the public queue.
Operational sites can also have a service agreement, customer planning record,
or completed connection rather than a current queue entry. Queue MW and Epoch
IT-power MW are different measurements and must not be summed as though they
were the same metric.

.github/workflows/sync_epoch_ai_data_centers.yml refreshes the three Epoch CSV
datasets daily at 07:30 UTC, on demand, and whenever index.html or the
crosswalk tooling changes. It refuses to publish a malformed/non-93 center
dataset and validates all inline dashboard JavaScript before committing.
Epoch states that its data are free to use, distribute and reproduce with
attribution under CC BY 4.0.

## Current data coverage -- read this before citing a number from the site

The published dashboard currently contains **1,558 row-level facilities / requests and 361.875 GW** across nine organized markets. A separate scope layer also records **83 additional MISO requests totaling 35.9 GW** whose public source omits required location fields; these are held outside the row-level table rather than assigned guessed geography. The resulting **expanded known scope is 1,641 requests / records and 397.775 GW**. The archived September 24 snapshot contains 1,802 rows and 420.2054 GW, but is retained separately and is not additive to current totals. The live GitHub Pages site is the publication surface; the exact row-level total is calculated from the embedded
`REGISTRY_DATA` array at page load.

| Source | Rows | GW | Origin | Read this before citing it |
|---|---:|---:|---|---|
| PJM | 37 | 7.6 | live queue export, 2026-09-26 | current accepted refresh |
| ERCOT | 714 | 154.8 | live GIS Report, 2026-09-26 | registry uses the GIS/interconnection product; not a complete per-project large-load register |
| SPP | 139 | 30.5 | GI active-request listing, Sept 2026 | applicant name is not published in the retained build |
| IESO | 30 | 10.0 | application status listing, Sept 2026 | exact capture time was not retained |
| MISO | 404 | 81.5 | GI Queue JSON, 2026-09-19 | 83 live >=100 MW requests (35.9 GW) lacked a published state and were excluded |
| CAISO | 63 | 23.1 | Cluster 15 request workbook, 2026-09-19 | **Cluster 15 only -- not CAISO's whole queue** |
| NYISO | 105 | 25.3 | interconnection queue workbook, 2026-09-19 | includes the Load Projects sheet |
| ISO-NE | 19 | 4.9 | IRTT public queue, 2026-09-19 | study stage is not published in the retained table |
| AESO | 47 | 24.2 | September 2026 Connection Project List | includes Data Load / Industrial Load rows |

### Data-universe completion

The project-level dataset now includes **60 BPA large-load request records** with public request identifiers, filed MW, POI text and status where the public cross-check exposes them. These are secondary reproductions of BPA public load-queue rows and remain non-additive.

The repository now includes a machine-readable **market universe manifest** at `data/market_universe_manifest.json` with a CSV companion. It explicitly separates what each operator publishes from what remains a disclosure limit.

The project-level layer has grown to **253 records**, with **252 mapped project records**. The only intentionally unlocated project-level record is the **Woostor LLC Alabama Power contract**, because the public contract evidence reviewed does not identify a site. A separate `data/supplemental_aggregate_map.json` adds **63 geographic evidence footprints**; those footprints are shaded on the map and explicitly labeled as non-facility evidence.

The 253 project records have one canonical `evidence_type` each. Current counts are:

- `secondary_large_load_request_record`: 60
- `environmental_permit_record`: 33
- `nyiso_gold_book_large_load_record`: 31
- `aeso_data_load_project_record`: 28
- `utility_data_center_forecast_project_record`: 28
- `caiso_large_load_interconnection_project`: 14
- `nyiso_load_project_site_record`: 12
- `utility_data_center_service_project`: 9
- `named_utility_load_project`: 8
- `ieso_load_application_record`: 6
- `utility_named_data_center_service_project`: 5
- `utility_service_project_secondary_capacity`: 3
- `utility_large_load_contract_record`: 3
- `secondary_data_center_interconnection_project`: 3
- `named_large_load_project_from_industry_list`: 2
- `iso_ne_forecast_large_load_project`: 2
- `named_utility_contract_project`: 1
- `named_utility_service_project`: 1
- `named_distribution_connection_project`: 1
- `utility_named_data_center_project`: 1
- `utility_data_center_service_area_record`: 1
- `utility_named_large_load_transmission_project`: 1

Those counts are generated from the canonical JSON and sum to exactly 253. They are evidence-source classifications, not facility categories. The canonical JSON record and its cited sources remain authoritative for every individual record.

The interactive map overlays **252 mapped project-level records** and separately represents the unlocated Woostor contract through a labeled Alabama regional evidence footprint. `data/map_layer_manifest.json` is the machine-readable inventory of every map overlay and its geometry/accounting treatment.

PJM large-load history is cataloged in `data/pjm_large_load_submission_history.json` with **28 public 2025–2026 LAS material entries**, preserving the utility submission/document trail without treating documents as facility rows.

CAISO historical coverage is now represented in `data/caiso_cluster_history.json` and CSV. The series contains 49 Cluster 8-and-prior projects, 27 Cluster 9, 21 Cluster 10, 30 Cluster 11, 44 Cluster 12, 60 Cluster 13 and 204 Cluster 14 projects — 435 projects and 121.204 GW in that historical series. A separately published Cluster 15 energy-only subset is recorded at 48 projects / 14.421 GW. These generator-queue figures are a distinct history layer and are not added to the large-load total.

The remaining hard limits are explicit rather than hidden: MISO's 83 additional >=100 MW requests remain unlocated in the accessible public response; ERCOT's Batch Zero process has public forms and eligibility/verification notices but not a public completed-response table; PJM's public service-request pages expose generation/merchant-transmission/long-term-firm service structures but do not establish a per-load-request dataset; SPP's HILL framework is public but its customer-level load list is not; ISO-NE publishes a small forecast table but not project-specific study stages. These are tracked as source/disclosure states, not silently converted into fake rows.



The repository also preserves public utility, regulator, planning, connection and permit evidence that cannot safely be collapsed into the core nine-market row-level total without double-counting or inventing missing fields. See `data/supplemental_large_load_evidence.json`.

Current examples include:
- MISO: 83 additional live >=100 MW requests (35.9 GW) lacking published location fields.
- Dominion Energy Virginia: approximately 70 GW of large-load DP Requests advancing through its connection queue at the end of 2025.
- ComEd: 16 GW of highly probable large-load interconnection requests in its 2026 planning material.
- Salt River Project: 80 projects above 10 MW totaling 15.308 GW, including 52 data-center projects totaling 14.140 GW.
- BC Hydro: 15 AI/data-centre applications representing close to 800 MW.
- Portland General Electric: five executed data-centre customer contracts totaling 430 MW.
- Entergy Louisiana/Hut 8: River Bend initial 330 MW utility capacity for 245 MW critical IT load, with potential scaling to 1 GW utility capacity.
- ISO New England: a 200 MW data-center project listed in the CELT 2026 large-load forecast.
- Virginia DEQ: a data-center air-permit identity inventory alongside reports of 72 operating data centers in Loudoun County and nine more in planning.
- Ontario: the IESO application-status universe and OEB Centralized Capacity Information Map are preserved as broader connection/grid-context layers.

Additional utility layers now include APS's reported 19 GW uncommitted extra-large-customer queue, AEP's 69 GW of contracted load growth through 2030, AEP Ohio's approximately 12 GW of new contracted load through 2030, the planned 10 GW Piketon data-center campus, Ameren Missouri's up-to-2 GW demand-planning envelope, and PacifiCorp's ongoing tens-to-hundreds-of-MW large-customer request stream. These remain supplemental and are not added to the core total without project-level deduplication.

The supplemental evidence file now contains **58 source/evidence units**, including the current CAISO full public-queue report metadata and additional BPA/PJM/ComEd/MISO utility and planning evidence. These units are not automatically additive.

These measures are **not summed** into a single "total capacity" because they have different units, vintages, geographic scopes, stage definitions and overlap relationships. The only direct additive expansion to the current row-level registry is the separately identified 83-record / 35.9 GW MISO population used in the expanded-known scope metric.

### Epoch connection research targets

Every one of the **93 canonical Epoch AI sites** now has a connection-research target record in `data/epoch_connection_research_targets.json` with grid jurisdiction, site-specific queue state, current site IT-power context, evidence count, source trail, coordinates and next research action. The companion `data/epoch_connection_research_targets.csv` is a flat export. The target layer is intentionally separate from verified queue membership: a dashed map target can mean only that the relevant queue/utility system is known.

The underlying Track 3 evidence inventory is preserved independently in `data/epoch_site_evidence_records.json` and CSV. It contains **68 discrete site-level evidence assertions across 59 of the 93 sites**. These assertions can identify utilities, public contracts, facility records or other site-specific evidence without establishing a formal queue ID. They are not additive capacity records.

On the map, the **Connection targets** toggle overlays all 93 research targets on the same site geometry as the Epoch layer. Target popups show the current grid jurisdiction, research state, queue ID/name where verified, site-specific capacity when known, evidence-item count, source links, and the next action. Geometry precision is carried through from the canonical Epoch map record.

### Project-level extraction

The repository has a dedicated project-level evidence layer at `data/project_level_extractions.json` with a CSV export at `data/project_level_extractions.csv`. It currently contains **241 individually identifiable records** extracted from public source material:

- **60 BPA large-load request records**, including publicly reproduced request IDs, filed MW, point-of-interconnection text and status where exposed.
- **33 Virginia DEQ issued-air permit records**, with permit number, named site/project, county and issuance date.
- **28 AESO Data Load projects**, with project IDs, project names, planning-area/town identities and public DTS/contract-capacity values.
- **12 NYISO Load Project records**, with queue ID, project/developer, MW, county and POI/site information where publicly exposed.
- **6 IESO load/increase-load application records**, including applicant, project name, zone, MW and target date.
- **8 AEP named customer/project records**, **2 EEI-listed projects**, **2 ISO-NE forecast project records**, and **3 named utility/service/contract/distribution records** (Project Camellia, River Bend AI campus, and Vaughan MTS #6), plus **28 historical ComEd data-center forecast rows**, **7 Dominion data-center service projects**, **9 additional NYISO Gold Book rows**, and **1 Idaho Power named data-center project**.

The project layer is deliberately **not additive** to the 1,558-row core queue table or the 1,641-record expanded-known scope. Multiple dated capacity claims inside one project are retained separately. No MW is inferred when a utility does not publish the load.

The interactive map now overlays **252 mapped project-level records** and separately represents the one unlocated Woostor contract as a labeled aggregate footprint. Map geometry is explicitly display geography (public site-area, town, county, state/province or country centroid), not an invented street address. A separate `data/supplemental_aggregate_map.json` layer adds **63 aggregate utility/regulatory and historical-queue footprints**, displayed as shaded areas and labeled as non-facility evidence.

The Epoch AI map layer contains **93 frontier-site observations** and is backed by the canonical `data/external/epoch_ai/site_level_connection_evidence.json` crosswalk. Of the 93 sites, **59 currently have site-level grid evidence records and 34 remain pending site-specific grid-record research**. The map popups expose the evidence status and available source links.

The remaining hard limits are explicit rather than hidden. MISO's 83 additional >=100 MW requests remain outside the row-level table because the captured public response lacks the state/location fields needed to make defensible site rows. ERCOT's Batch Zero process is public, but completed RIOO responses are not exposed as a public per-project table. PJM's public Load Analysis Subcommittee materials provide a dated utility-submission history, but they do not establish a public per-load-request database. SPP's HILL process is public without a customer-level public load list. ISO-NE's forecast material names large-load projects but does not publish a complete project-specific study-stage history.

### PJM large-load submission history

`data/pjm_large_load_submission_history.json` and its CSV companion preserve **28 public 2025–2026 PJM Load Analysis Subcommittee material entries**, including the named utility large-load/data-center submission trail from the September 2025 and September 2026 meetings. These are document/evidence records, not unique facilities or additive MW rows.

### CAISO historical queue coverage

`data/caiso_cluster_history.json` and its CSV companion preserve a historical generator-interconnection series covering Cluster 8-and-prior through Cluster 14: **435 projects / 121.204 GW** in the historical series. A separately published Cluster 15 energy-only subset is recorded at **48 projects / 14.421 GW**. The current full CAISO Public Queue Report is linked from the dashboard as the source for future complete row-level refreshes; historical series values are kept separate and non-additive.

### Additional utility-linked projects

The project layer also includes six newly extracted utility-linked records outside the organized-market core: Google/Xcel's Pine Island, Minnesota data center; Google's West Memphis, Arkansas data center; AWS's Clinton, Mississippi data center; QTS Bessemer / Project Marvel; Cloverleaf Infrastructure's Project Red Clay; and the Sovereign Gazelle/Somerville large-load project. Source-specific capacity claims are retained only where the cited public record provides them; associated generation additions are not relabeled as data-center load.

### Supplemental public large-load evidence

The supplemental evidence file now contains **55 source/evidence units**. The website provides a searchable browser for all of them. These include MISO's unlocated requests, utility pipelines, regulatory aggregates, planning forecasts, connection/process sources, permit inventories, ERCOT Batch Zero source material and non-RTO utility evidence. The measures are not summed because their populations, dates, units and overlap relationships differ.

## Regulatory filings section

`index.html`'s "Regulatory filings" section links to two PDFs by filename:

- `FERC_Docket_RM26-4-000_Comments_Computational_Load_Telemetry.pdf`
- `BIS_Rulemaking_Petition_5USC553e_Computational_Load_CEII_Protocol.pdf`

The links are live (`available: true` in the `FILINGS` array near the
bottom of `index.html`), and both PDF files are now present in the repository
root with those exact filenames.
Place both files, with those exact names, in the same directory as
`index.html` (the repository root) before deploying, or the two Download
buttons will 404. The monthly workflow fails if either link stops being marked
`available: true` in `index.html`, and raises a warning if either PDF is not in
the repository root.

## Automated monthly refresh

`.github/workflows/monthly_registry_update.yml` runs at 06:00 UTC on the 1st of
every month and on demand (Actions tab, *Monthly Registry Update*, Run
workflow; tick `dry_run` to execute everything without committing). It checks
out the repo, sets up Python 3.12 with a pip cache, installs
`requirements.txt`, runs the self-tests of `ingest_grid_queues.py`,
`compute_anomaly_detector.py`, `investigate_ambiguous_loads.py` and
`guard_registry_refresh.py`, fetches every live feed, estimates compute load,
gates each RTO, embeds the accepted RTOs into `index.html`, and checks the two
regulatory PDF links. Then, only on `main` and only if `index.html` or the two
CSVs in `data/` changed, it commits and pushes as
`Automated Monthly Registry Sync: [YYYY-MM-DD]`. Logs and the fresh outputs are
attached to every run for 30 days.

**Live validation status.** A production live-feed run completed successfully on
September 26, 2026. All four offline self-test stages passed, the live ingest
completed, the per-RTO refresh gate completed, and the registry update was
committed. For future changes, a manual run with `dry_run` ticked remains the
safe way to inspect the refresh gate before allowing publication. Some RTO
sites may also refuse requests from GitHub-hosted runners; that shows up as an
unavailable feed, not as a failure.

Each RTO ends a run in one of three states:

| Outcome | When | Effect |
|---|---|---|
| accepted | fresh row count and capacity are within 50%-200% of what `index.html` holds, or the RTO is new | its rows are replaced |
| unavailable | the run produced no rows for it (blocked, moved or failed feed) | previous rows kept; a warning is raised |
| rejected | outside that range, unknown RTO label, duplicate queue IDs, unreadable capacity, or the raw and enriched CSVs disagree | previous rows kept; an error is raised; the other RTOs are still committed and the run then ends red |

The two CSVs the workflow commits (`data/registry_raw.csv`,
`data/computational_load_estimates.csv`) hold only the RTOs accepted in the
latest run; `index.html` is the cumulative registry. Automated runs do not
record a SHA-256 of each raw capture the way `data/SOURCES.md` does for the
v2.0 build; the run log and the git history are the record. The thresholds are
the `--min-ratio` / `--max-ratio` arguments of the `guard_registry_refresh.py`
call.

Requirements: GitHub Actions enabled for the repository, no secrets, and a
`main` branch that accepts pushes from `github-actions[bot]` (a rule that
requires pull requests will make the final push fail).

## Investigating the ambiguous tier

`investigate_ambiguous_loads.py` turns the "genuinely ambiguous" large loads
into a worklist, `ambiguous_facilities_dossier.md`:

```bash
python investigate_ambiguous_loads.py                    # all nine sources, from index.html
python investigate_ambiguous_loads.py --input data/computational_load_estimates_new5.csv
                                                         # adds POI, status, technology and dates for those RTOs
python investigate_ambiguous_loads.py --rto PJM,ERCOT,SPP,IESO   # the original four sources
python investigate_ambiguous_loads.py --top 25 --engine bing --json leads.json
python investigate_ambiguous_loads.py --selftest
```

It reads the registry embedded in `index.html` (all nine RTOs) and lets an
enriched CSV replace the rows of the RTOs it contains, so a partial CSV never
drops an RTO. It keeps records with `capacity_mw >= 100`, tier `Genuinely
Ambiguous / Unclassified Large Load` and entity category `Developer Not Matched
To Known List` or `Developer Not Disclosed`, largest first. In this build that
is **141 facilities (53.9 GW)**: NYISO 38, MISO 36, AESO 30, IESO 25, SPP 12.
The "38" quoted for the first four sources is the four-source tier count; under
this filter those sources give 37, because IESO `2026-866` (Project ONT1, 450
MW) has a developer that resolved to a known colocation developer and is
excluded. PJM and ERCOT contribute none.

For each facility the dossier has up to seven search leads -- municipal council
minutes and zoning approvals, environmental and utility-regulator registries,
substation and interconnection filings -- worded for that jurisdiction (an
Ontario rezoning is a "zoning by-law amendment", an Alberta one a
"redesignation"). The script makes no network requests and verifies nothing: a
lead is a search, not a finding.

**Recording a verified identity.** When a person confirms a facility from a
public record, add an entry to `ground_truth_overrides.json` (format:
`ground_truth_overrides.example.json`) with `rto`, `queue_id`, a
`verified_label`, `confirmed_by`, `confirmed_on` and at least one `evidence`
citation. The allowed labels are Confirmed Data Center Campus; Confirmed
Industrial Park / Manufacturing; Confirmed Utility / Distribution Load Growth;
Confirmed Cryptocurrency Mining; Confirmed Other Large Load; Ruled Out
(Duplicate / Withdrawn / Data Error). Re-run and the facility gets a VERIFIED
block with the label and citations. An entry with no evidence, an unknown
label or a mistyped key stops the run (exit code 2) and lists every problem; an
entry that matches nothing in the registry is listed in the dossier's audit
section. Overrides change only the dossier -- not the CSVs, the tier
classification or the dashboard.

## Running the pipeline

```bash
pip install -r requirements.txt
python ingest_grid_queues.py --selftest
python compute_anomaly_detector.py --selftest
python ingest_grid_queues.py --pjm-file <path> --ercot-file <path> \
    --miso-file miso_gi_queue.json --caiso-file <cluster xlsx> \
    --nyiso-file <queue xlsx> --isone-file irtt.html --aeso-file <project list xlsx> \
    --include-raw-fields --output registry_raw.csv
python compute_anomaly_detector.py --input registry_raw.csv --output computational_load_estimates.csv
python embed_registry_data.py --raw registry_raw.csv --enriched computational_load_estimates.csv
```

Sources without a `--*-file` flag are fetched live. For a partial refresh,
run the two scripts on just the files you have and `embed_registry_data.py`
replaces only those RTOs in `index.html`.

To produce the dossier after a refresh: `python investigate_ambiguous_loads.py`.

## Deploying the dashboard

`index.html` is fully static and self-contained -- no server, no build,
no API keys. Open it directly in a browser, or serve the repository root
with any static host. See the GitHub Pages instructions provided alongside
this archive.

## License

Apache License 2.0 -- see `LICENSE`.

## Contact

grid.telemetry.initiative@gmail.com


**Map coverage:** `data/project_level_map.json` contains 252 mapped project records out of 253 project-level records; the sole unlocated project is explicitly documented. `data/supplemental_aggregate_map.json` contains 63 aggregate/historical records and currently has numeric display coordinates for all 63. Coordinate precision is retained per record; a centroid/display point is never presented as a street address.


Map-layer accounting is published in `data/map_layer_manifest.json` and `data/map_layer_manifest.csv`.
