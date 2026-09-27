# Track 3 — Complete Coverage Inventory

Updated: 2026-09-27

## Scope

This repository is an independent open-source public-evidence and data-engineering contribution relevant to the broader Track 3 problem described by the AI Futures Project. It is **not** an AI Futures Project publication, formal Track 3 implementation, certification authority, treaty verifier, or proof that secret compute has been comprehensively detected.

Official public references:

- https://ai-2040.com/supplements/verification-plan/get-involved
- https://ai-2040.com/print/covert-ai-projects

The AI Futures material describes Track 3 as verifying the absence of secret compute and, in the covert-projects supplement, emphasizes three linked tasks: accounting for pre-deal compute production; tracing sales/resales to physical end use; and locating remaining unaccounted compute with incentives and aerial imagery. Appendix B adds threshold audits, random sampling of the small-owner tail, physical inspection, serial continuity, decommissioning/recycling controls, an untraced pool, and a statistical certificate.

## Repository implementation inventory

| Track 3 element | Current implementation | State | Blocking gap |
|---|---|---|---|
| Pre-deal AI-compute accounting | Aggregate owner/user/sales/component snapshots + site layer | PARTIAL | No globally exhaustive transaction-level inventory |
| Inputs to accelerator production | Component and supply-denominator snapshots | INGESTED_SNAPSHOT | Inputs are estimates/constraints, not complete vendor declarations |
| Vendor sales accounting | Chip-type, organization, and timeline snapshots | INGESTED_SNAPSHOT | No global invoice/serial ledger |
| Sales/resales to physical end use | Entity graph + site evidence + research packets | PARTIAL | Public transfer/resale records are incomplete |
| Audit owners above threshold T | Parameterized audit-population protocol | FRAMEWORK_IMPLEMENTED | Threshold and closed population must be externally fixed |
| Random sample of small-owner tail | Deterministic sampling protocol | FRAMEWORK_IMPLEMENTED | No closed population/sample outcome yet |
| Physical inspection | Inspection schema + chain of custody | FRAMEWORK_IMPLEMENTED | No authorized public inspection observations |
| Serial-number continuity | Lifecycle state machine + integrity rules | FRAMEWORK_IMPLEMENTED | No global public serial ledger |
| Decommissioning/recycling | Verification-state protocol + WEEE source catalog | FRAMEWORK_IMPLEMENTED | No independently verified compute-specific ledger |
| Untraced compute pool L | Residual ledger + certificate model | FRAMEWORK_IMPLEMENTED | Global transaction chain is not closed |
| Locate remaining unaccounted compute | Optical/TIR/SAR + queue surveillance + case workflows | PARTIAL | Public imagery cannot prove universal absence; 25/93 reference sites lack retained derived observations |
| Incentive/amnesty/buyback evidence | Disclosure protocol | FRAMEWORK_IMPLEMENTED | No verified program/event dataset |
| Physical data-center discovery | Epoch reference + broader queue surveillance + public records | PARTIAL | No intelligence corpus or global covert-site census |
| Power/cooling/infrastructure corroboration | Annual power, cooling, transformer, substation/transmission evidence | PARTIAL | Interval telemetry and exhaustive site linkage are incomplete |
| Independent corroboration | Provenance/conflict layer | PARTIAL | Independence has not been independently assessed across all sites |
| Global coverage | Global chip/source layer; North American physical registry | PARTIAL | Site-level physical coverage remains primarily North American |
| Statistical certificate | Transparent tail-bound calculator | FRAMEWORK_IMPLEMENTED | Requires closed population, defined failures, reproducible sample, validated evidence |

## Current empirical layers

- 93-site Epoch frontier-AI reference universe.
- 423 retained derived remote-sensing observations across 68 of 93 reference sites.
- 149 optical scene observations, 136 TIR observations, 138 SAR observations.
- 211 current physical/research observation tasks.
- 6 site-level annual electricity-consumption snapshots.
- 2 structured site-level cooling snapshots in the cooling-observation file.
- 3 source-backed transformer event records.
- 90 substation-related and 113 transmission-related external evidence records.
- 83 sites with retained chip-inventory records; 10 sites remain unknown.
- 4 sites with site-specific compute-tenancy snapshots; 89 remain unknown.
- 17 sites with retained service/contract evidence; 76 remain not ingested.
- 14 sites with retained site-level regulatory evidence; 79 remain not assessed.
- 2 defensible site-specific queue IDs in the 93-site Epoch crosswalk.
- 141-record broad ambiguous-load research pool totaling 53.8512 GW under the repository's current filter.
- 68 of those 141 have an explicit retained load-side technology field; 73 require project-type adjudication before strict load-discovery admission.

## Closed-case laboratory

The current closed-case set contains:

- AMB-NYISO-1765 — manufacturing/industrial outcome with bounded applicant mismatch.
- AMB-NYISO-1745 — data-center identity outcome.
- AMB-IESO-2026-903 — deliberately inconclusive at the physical-targeting stopping rule.

Every case separates:

`queue → entity → location → public evidence → physical observation → electrical/transformer → adjudication`

A closed case does not require every evidence layer to be positive. It requires each declared gate to reach a terminal evidence state.

## Discovery queue

The strict admitted queue contains five cases:

- P3066 — Leedale Data Load
- P3198 — Lynx Data Load
- P3108 — Wild Rose Power Hub Load
- P2958 — Hydrogen Canada MPC Load (industrial control)
- P2614 — Dow Fort Sask. Load (industrial control)

These are not ranked for hiddenness or expected outcome. The first three are ambiguity targets; the last two test whether the workflow correctly resolves large non-data-center loads.

## Evidence semantics

The registry never silently converts:

- interconnection MW → measured electricity;
- measured electricity → compute;
- company ownership → physical site presence;
- public lead → canonical evidence;
- missing public record → evidence of absence;
- source availability → observation;
- aggregate owner snapshots → site inventory.

`UNKNOWN`, `NOT_TESTED`, `NO_PUBLIC_RECORD`, and `SOURCE_AVAILABLE_NOT_INGESTED` are preserved as research states.

## What still requires capability beyond public registry data

A true Track 3 implementation additionally needs trusted access to records and processes that this repository cannot create from public web evidence alone:

- complete accelerator-vendor declarations;
- transaction-level sales/resale/transfer records;
- globally consistent asset/serial identifiers;
- physical inspections under agreed authority;
- verified recycling/destruction records;
- intelligence reporting for specifically concealed facilities;
- a closed statistical sampling population;
- independently operated verification/certification authority;
- international procedures for disputes, audits, notice, access, and enforcement.

Those are not represented as complete merely because a schema exists.

## Completion criterion

This repository should be described as **Track-3-relevant research infrastructure** until the blocking gaps above are materially resolved.

The project is complete at the repository engineering level when every requirement has:

1. a machine-readable artifact;
2. a reproducible builder or validator where feasible;
3. explicit evidence semantics;
4. a current status;
5. a documented blocking gap when external capability is required;
6. no claim of empirical verification stronger than the retained evidence.
