# Track 3 Ambiguous-Load Closure Pilot

Purpose: close a small, deliberately selected subset of the registry's genuinely ambiguous large-load tier end-to-end before expanding coverage.

## Selection rule

The pilot starts from the repository's 141-facility Genuinely Ambiguous / Unclassified Large Load dossier (>=100 MW; developer not matched to the known entity list or not disclosed). Pilot cases maximize methodological diversity and public-record tractability rather than simply selecting the largest loads.

| RTO | Queue ID | Project | MW | Pilot role |
|---|---|---|---:|---|
| NYISO | 1765 | Micron Fab 3 | 606 | Entity-resolution stress test; manufacturing outcome |
| NYISO | 1745 | Pontoon Bridge Road Data Center | 250 | Data-center identity outcome |
| IESO | 2026-903 | Project IQ197 | 1,380 | Intentionally unresolved/unknown outcome |
| IESO | 2025-854 | CPXP Sarnia Hydrogen Facility | 130 | Non-data-center industrial outcome; control case |

The first three form the minimum closure set. Case 4 is included because it is unusually well named but was still classified as ambiguous by the registry entity-matching layer.

## Closure gates

A case is closed only when every gate has a terminal, source-backed state. A gate may conclude with FOUND, NO_PUBLIC_RECORD, or INCONCLUSIVE; closure does not mean a positive finding.

1. Queue record: exact ID, capacity, status, project name, applicant, POI/electrical geography, and primary source.
2. Entity resolution: legal/entity identity or documented mismatch without guessing.
3. Location: exact public address/coordinates when available; otherwise explicit coarse precision. Never use a county/zone centroid as a facility coordinate.
4. Public-record search: operator, municipal, environmental/regulatory, company, planning, and infrastructure records with URL, dates, and claim scope.
5. Satellite/physical pull: public STAC acquisition against the defensible coordinate, retaining scene IDs, dates, collection, processing version, and compact metrics.
6. Transformer/electrical check: project-specific transformer/substation procurement, delivery, installation, energization, and utility work. No record is recorded as NO_PUBLIC_EVENT_FOUND, not absence.
7. Adjudication: CONFIRMED_DATA_CENTER; CONFIRMED_OTHER_LARGE_LOAD; CONFIRMED_MANUFACTURING_OR_INDUSTRIAL; INCONCLUSIVE_AFTER_SEARCH; or RULED_OUT_DUPLICATE_WITHDRAWN_OR_DATA_ERROR.
8. Boundary statement: explicitly state what remains unknown and why a stronger claim is not justified.

## Stopping rule

Close after the primary sources are checked; the municipal/regulatory/company search ladder is run; the best physical coordinate is established or its absence recorded; satellite pull succeeds or records a documented failure; transformer searches have a terminal status; and conflicting identity evidence is recorded. Do not keep searching indefinitely to manufacture a desired answer.

## Record schema

Each case contains case_id, rto, queue_id, project_name, capacity_mw, pilot_role, initial_registry_classification, queue, entity_resolution, location, public_evidence[], physical_observations[], transformer_check, adjudication, unresolved_items[], methods_note, last_verified_on.

## Interpretation rule

A closed case demonstrates that the workflow can move an ambiguous registry row to a documented disposition. It does not establish detection completeness, covert-compute detection, or facility-wide verification beyond the evidence actually observed.
