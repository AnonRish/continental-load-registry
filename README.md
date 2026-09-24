# Continental Large-Load Interconnection & Telemetry Registry

**Version 2.1** -- adds the automated monthly refresh and the ambiguous-facility
investigation engine on top of the v2.0 nine-source registry.

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
  for the full flag list, or `--selftest` to run the suite (122 checks)
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
- `index.html` -- the public dashboard. Single-file, Tailwind (CDN) +
  vanilla JS, no build step. The registry table's data is embedded
  directly in the file (by `embed_registry_data.py`), not fetched at
  page-load. Prose that quotes a count or a GW figure is filled in from
  that data at load time, so a re-embed cannot leave a stale number behind.
- `.github/workflows/monthly_registry_update.yml` -- (2.1) refreshes the
  registry from the live feeds on the 1st of every month, 06:00 UTC, or on
  demand, and commits the result to `main`. See "Automated monthly refresh".
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
- `data/` -- the five most recently added sources' outputs
  (`registry_raw_new5.csv`, `computational_load_estimates_new5.csv`) and
  `SOURCES.md` (URLs, capture time, SHA-256 of each parsed file). The raw
  captures themselves are not bundled. The monthly workflow also writes
  `registry_raw.csv` and `computational_load_estimates.csv` here.
- `requirements.txt` (unchanged: the 2.1 scripts use only the standard library), `LICENSE` (Apache 2.0).

## Current data coverage -- read this before citing a number from the site

The dashboard reflects **all nine sources**: 1,802 facilities, 420.2 GW. (That
is the v2.0 snapshot and the table below is static text; once the monthly
workflow has run, the dashboard's own figures -- filled in from its embedded
data -- are the current ones.)

| Source | Rows | GW | Origin | Read this before citing it |
|---|---:|---:|---|---|
| PJM | 281 | 66.0 | queue export, Aug 2026 | unchanged |
| ERCOT | 714 | 154.8 | queue export, Aug 2026 | unchanged |
| SPP | 139 | 30.5 | `GenerateActiveCSV`, Sept 2026 | unchanged; no applicant name |
| IESO | 30 | 10.0 | `applicationstatusdata.json`, Sept 2026 | unchanged |
| MISO | 404 | 81.5 | `/api/giqueue/getprojects` JSON, 2026-09-19 | 83 live requests (35.9 GW) **excluded**: no state published |
| CAISO | 63 | 23.1 | Cluster 15 request workbook, 2026-09-19 | **Cluster 15 only -- not CAISO's whole queue** |
| NYISO | 105 | 25.3 | queue workbook, 2026-09-19 | includes its Load Projects sheet (38 loads, 13.5 GW) |
| ISO-NE | 19 | 4.9 | IRTT public queue page, 2026-09-19 | no study stage; 2 NY-sited duplicates excluded |
| AESO | 47 | 24.2 | Connection Project List (Sept 2026), 2026-09-19 | 30 loads (20.4 GW); 27 of 28 data loads have no date |

PJM, ERCOT, SPP, and IESO are as they were in the previous build (the
SPP/IESO note in that build -- fetched from the live endpoint outside the
script and parsed by the same code -- still applies). MISO, CAISO, NYISO,
ISO-NE, and AESO were parsed from five raw files captured 2026-09-19
(`data/SOURCES.md`), and are the first sources written against real files
rather than documentation. `--miso-file` / `--caiso-file` / `--nyiso-file` /
`--isone-file` / `--aeso-file` are the tested path; the `fetch_*_bytes()`
helpers behind them are plain GETs of the same URLs that have **not** been
run from inside the script (the environment that wrote them cannot reach
those hosts).

What the new sources do and do not tell you:

1. **CAISO is Cluster 15 only.** The file is the Cluster 15 request list (86
   live requests). Earlier clusters and serial projects still in CAISO's
   queue are not in it. CAISO's 63 rows are a floor, not its queue; the
   whole-queue workbook is the next thing to add.
2. **MISO withholds detail on its newest requests.** All of DPP-2026, plus a
   few others, publish no state, county, POI, or technology. 83 live
   requests of >=100 MW (35.9 GW) have no state and fail the registry's
   requirement that every row carry one; they are excluded, and the ingest
   log says so (`schema_rejected=83` plus a WARNING with the MW), rather
   than a state being guessed from the transmission owner. 36 more (8.6 GW)
   state a location but no technology and are kept, in the ambiguous tier.
   If you would rather show the 83 with an "unknown" state, that is a change
   to the state validator, not to the adapter.
3. **Only NYISO names the applicant** (of these five). MISO, CAISO, ISO-NE,
   and AESO publish none, so "Developer Not Disclosed" on those rows is a
   property of the source, not a finding about the developer.
4. **NYISO and AESO carry load requests, not just generator-queue rows.**
   NYISO's Load Projects sheet (named developers, peak MW, an End-Use code
   such as `DAT-AI`) and AESO's `Data Load` / `Industrial Load` rows are
   loads. The End-Use is carried into `raw_fuel_technology` (`Load - Data
   Center (AI)`, `Load - Manufacturing (Microchip Fabrication)`), so a chip
   fab and an AI data center are not the same line. Non-data-center loads are
   kept -- "industrial" and "large load" are on the spec's accept list -- but
   labeled as what NYISO says they are.
5. **ISO-NE:** capacity is `Net MW`, not `Summer MW`, because ISO-NE lists
   capacity-rights-only requests (Net MW 0, Summer MW hundreds) that duplicate
   another queue position. Two requests sited in New York that appear only
   for capacity rights (QP 1595 and QP 1596) are the same projects as NYISO's
   C24-148 and C24-304-004 and are excluded so 450 MW is not counted twice.
6. **Status mapping is informed judgment, not a literal translation**, and is
   documented at each mapping (`derive_miso_status`, `derive_nyiso_status`,
   `derive_aeso_status`): e.g. MISO `Done` with post-GIA work not yet
   complete, NYISO 10-12 (through *Under Construction*), and AESO stages 4-5
   all land in "IA in Progress", the most advanced pre-operational bucket,
   the same call the SPP and IESO adapters already make.

With all nine sources, 142 facilities (54.3 GW) land in the genuinely
ambiguous tier -- unresolved developer, no storage signal -- versus 38
(11.8 GW) with the first four. 104 of the 142 come from the new sources:
NYISO's loads (38, 13.5 GW), AESO's loads (30, 20.4 GW), and MISO's
unclassified rows (36, 8.6 GW). That is stated loads and undisclosed
technology, not evidence about any specific facility; see the dashboard's
Methodology section for what the tier does and doesn't mean.

Two of the location columns are not municipalities. For IESO the `county`
column holds the IESO electrical zone (`Essa`, `West`, `Toronto`, `Southwest`,
`East`, `Northeast`); `Essa` is one of IESO's ten zones, not the Township of
Essa. For AESO it holds the planning area, a hub named for a town. Searching
either as a place name produces confident but wrong answers, and
`investigate_ambiguous_loads.py` deliberately does not.

"Continental" in this repo's name now spans all nine organized markets, but
not utilities outside them.

Bugs found by running real data through the code, fixed, and covered by new
self-test checks (the earlier build's two parsing bugs are described in
`ingest_grid_queues.py`'s docstring and the `_clean_cell` / header-detection
comments):

- `titlecase_county` turned real county names into `MacOn`, `MacOmb`,
  `MacOupin`, `MacKinac` (a `MacXxx` rule that never matched a real county)
  and flattened `DeKalb` / `LaSalle` / `DuPage`. **One row already in the
  published table was affected -- PJM `C01-2046`, IL, `MacOn` -- and is
  corrected to `Macon` in this build.** It also now capitalizes both halves
  of AESO's `Strathmore/Blackie`-style planning areas.
- The shared generation-technology reject list missed `Diesel`,
  `Waste Heat Recovery`, and `High Voltage DC` (real MISO values), which fell
  through the accept-unclassified default; a separate additive layer now
  rejects them for the five new sources only, so PJM/ERCOT/SPP/IESO
  filtering behaves as before.
- The state map covered only the PJM/ERCOT/SPP footprint; NYISO writes
  `New York` in full on a row, which would have dropped it.
- NYISO cells carry non-breaking spaces (`TransGrid\xa0Energy\xa0LLC`), so a
  search for a name with a plain space would never match; text cells are now
  normalized, and one MISO POI with a UTF-8-as-cp1252 en dash is repaired.
- `classify_status("Inactive")` returns "Active" (it matches the substring
  "ACTIVE"). The five new adapters use their own status classifiers and do
  not touch it; the four earlier sources' raw files were not available for
  this update, so whether any of them contains an "Inactive" status was not
  checked. Noted here, not changed.

Found while building 2.1 (documented, not changed):

- `compute_anomaly_detector.py` raises `KeyError: 'review_priority'` when its
  input CSV has a header but no rows (for example when every source is filtered
  out). The monthly workflow checks for an empty CSV first and stops with a
  readable message instead.
- `ingest_grid_queues.py` exits 0 when some sources fail and others succeed (it
  exits 1 only if every source fails), and its output simply lacks the failed
  RTOs. That is why the workflow gates each RTO with `guard_registry_refresh.py`
  instead of trusting the exit code.

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

**Read this before relying on it.** None of the nine `fetch_*()` helpers has
been run against its live server from inside `ingest_grid_queues.py` (see that
file's docstring), so the first real run is their first test. Start with a
manual run with `dry_run` ticked and read the "Registry refresh gate" table in
the run summary. Some RTO sites may also refuse requests from GitHub-hosted
runners; that shows up as an unavailable feed, not as a failure.

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
