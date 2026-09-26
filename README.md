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

## Current data coverage -- read this before citing a number from the site

The published dashboard currently contains **1,558 facilities and about
361.9 GW** across nine organized markets. The live GitHub Pages site is the
publication surface; the exact total is calculated from the embedded
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
bottom of `index.html`), but **this archive does not contain the PDF
files themselves** -- they weren't accessible to bundle at build time.
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
