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

### Supplemental public large-load evidence

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

These measures are **not summed** into a single "total capacity" because they have different units, vintages, geographic scopes, stage definitions and overlap relationships. The only direct additive expansion to the current row-level registry is the separately identified 83-record / 35.9 GW MISO population used in the expanded-known scope metric.

### Facility research records

Every row visible in the dashboard has a corresponding JSON research record
under `data/facility_records/`. The record schema is deliberately broader than
the table display and includes the union of fields available from the registry
and enrichment pipeline:

`queue_id`, `rto_region`, `state_province`, `county_or_zone`,
`poi_substation`, `capacity_mw`, `projected_date`, `status`, `project_name`,
`developer_entity`, `raw_fuel_technology`, `entity_category`,
`matched_public_entity`, `entity_match_score`, `load_type_tier`,
`transmission_owner`, `in_known_high_density_zone`,
`project_name_keyword_hits`, `reached_ia_stage`, low/reference/high GPU
estimates, low/reference/high 90-day FLOPs estimates,
`clears_1e26_flops_all_scenarios`, `review_priority`, and `review_reason`.

The research record also contains:

- **Retained source-field extract:** when the repository has a raw-field CSV
  row, the record preserves those source columns and their values exactly as
  represented in that retained CSV.
- **Source and capture metadata:** publisher, official source URL, optional
  publisher page, capture date and precision, source scope, and snapshot hash
  where one exists.
- **Provenance trail:** source -> retained extract -> `ingest_grid_queues.py`
  normalization -> `compute_anomaly_detector.py` enrichment -> dashboard /
  research-record publication.
- **Explicit missingness:** a field that was not published or whose original
  source bytes were not retained stays null / unavailable. The builder never
  reconstructs a normalized value and labels it as an original publisher
  value.

This distinction matters. **1,389 of the 1,558 records currently have a
retained ingest-level source-field row** in the repository (PJM, ERCOT, MISO,
CAISO, NYISO, ISO-NE, and AESO). **169 records (SPP + IESO) do not have the
original source row retained.** The per-record source metadata still links to
the relevant official publisher source.

The current committed enriched CSV covers **751 records (PJM + ERCOT)**.
Other RTO records still receive the complete normalized schema, but enrichment
fields that were not retained for that source are left unavailable; the
low/high compute-range fields are recomputed from normalized MW using the
documented scenario constants and marked in the record provenance.

To verify the research-record layer independently:

```bash
python build_facility_records.py --check
```

The monthly refresh runs this same check after embedding the registry, so the
record count must continue to match the published dashboard before the commit
step.


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
