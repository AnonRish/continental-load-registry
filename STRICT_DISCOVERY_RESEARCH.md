# Strict Discovery Research Queue

Updated: 2026-09-27

## Purpose

This is the operational queue for the next ambiguous-load closure cases. It sits downstream of the broad 142-record ambiguity pool and upstream of final adjudication.

A candidate is admitted only when a retained public source identifies the underlying request as a load-side project. Developer non-disclosure, large MW, or proximity to a known data-center cluster are not sufficient.

## Standard case sequence

1. Reproduce the source-level load classification.
2. Resolve project, applicant, developer, owner, and end-use identities without collapsing distinct roles.
3. Establish a defensible physical parcel or site coordinate.
4. Search permits, land records, utility/regulator filings, planning records, and independent corroboration.
5. Run physical observations only after the location gate closes.
6. Search transformer, service, substation, and construction evidence.
7. Adjudicate or stop at an explicit boundary.

## P3066 — Leedale Data Load

Queue: AESO P3066 · 1,864 MW · Load · Clearwater County · POI 38-Caroline.

Current public sources identify P3066 as a load project. A separate public facility record describes it as a proposed data center, while the retained queue surface does not expose a developer/owner or defensible facility coordinate. The immediate research target is physical targeting and entity resolution.

Sources:
- https://www.interconnection.fyi/project/aeso-p3066
- https://www.datacenter.fyi/public-record/p3066-leedale-data-load-764c0be1
- https://gridlens.ca/substation/378S

Do not infer: Clearwater County or Caroline planning context is not the facility coordinate; a secondary data-center label is not developer/operator proof; 1,864 MW is not measured electricity use or IT power.

## P3198 — Lynx Data Load

Queue: AESO P3198 · 1,800 MW · Load · Strathcona County / Fort Saskatchewan planning context · POI 33-Fort Saskatchewan.

Current public sources identify P3198 as a load project, but the developer is not exposed in the retained public queue surface. GridLens provides useful planning/substation context; it does not by itself establish the project parcel.

Sources:
- https://www.interconnection.fyi/project/aeso-p3198
- https://gridlens.ca/substation/439S
- https://gridlens.ca/substation/233S

Do not infer: a planning-area association is not a parcel match; a similarly named GLDC project is not automatically P3198; 1,800 MW is not measured demand.

## P2970 — Beacon Langdon A.I. Hub 2 Load

Queue: AESO P2970 · 1,400 MW · Load · Calgary/Langdon planning context.

This is an explicit AI/data-load candidate whose retained queue record does not expose a developer/owner. The research question is entity and physical resolution, not whether AI language appears in the project title.

Search sequence: AESO connection records → Alberta municipal planning/development records → land/property records → utility/regulator filings → independent facility registries.

Do not infer: AI wording does not establish operator, user, hardware, or measured consumption; planning area does not establish a physical parcel.

## NYISO 1743 — St. Lawrence Infrastructure 2

Queue: NYISO 1743 · 1,935 MW · Load · St. Lawrence County · POI NYPA Moses Massena 1/2.

Public records explicitly identify this as a load request. Independent public trackers already associate it with data-center/AI development, so the closure objective is physical/entity/infrastructure resolution rather than first discovery of a data-center project.

Sources:
- https://www.interconnection.fyi/project/nyiso-1743
- https://www.nysrc.org/wp-content/uploads/2026/02/9.1-DER-Report-Feb-2026-for-NYSRC-Exec-Committee-Final-Attachment-9.1.pdf
- https://www.stlawco.gov/sites/default/files/Planning/Trainings/LGC%202025%20Planning%20%26%20Zoning%20Presentation%20-%20Final.pdf

Do not infer: county or POI equals physical site; secondary classification establishes operator or compute; queue MW equals actual electricity or compute.

## NYISO 1742 — St. Lawrence Infrastructure 1

Queue: NYISO 1742 · 860 MW · Load · St. Lawrence County · POI NYPA HA-2 345 kV.

Use the same closure sequence as 1743, with particular attention to utility/transmission-owner records and physical parcel resolution.

Sources:
- NYSRC large-load report
- Current public NYISO queue mirror
- https://www.stlawco.gov/sites/default/files/Planning/Trainings/LGC%202025%20Planning%20%26%20Zoning%20Presentation%20-%20Final.pdf

Do not infer: county/POI equals physical site; aggregator labels establish legal ownership; queue capacity equals operating load.

## Closure output

Every completed case should emit:

case_id → source set → raw observations → normalized fields → physical artifacts → electrical evidence search → adjudication → unresolved boundaries

A case may legitimately end as inconclusive. The stopping rule is part of the result.
