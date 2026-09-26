# Epoch AI secondary evidence layer

This directory preserves the public Epoch AI AI Data Centers dataset separately
from the nine-market interconnection registry.

Epoch's AI data-center hub was updated September 24, 2026 and currently covers
93 major AI data centers. Epoch says the dataset is built from satellite
imagery, permits, public documents, company disclosures, regulatory filings and
other evidence. The main table contains site identity, current H100-equivalent
compute, current IT power, ownership/user information, sources and location;
separate timeline and chip-quantity datasets contain dated construction/power/
compute records and chip-level records.

## Files

- data_centers.csv — exact downloaded Epoch AI AI Data Centers table.
- data_center_timelines.csv — exact downloaded timeline table.
- data_centers_chip_quantities.csv — exact downloaded chip-quantity table.
- registry.json — normalized 93-site registry with raw main-table values, latest available timeline row, latest chip quantities by chip type, source metadata and conservative queue crosswalk.
- crosswalk.csv — exactly one row per Epoch site.
- manifest.json — access date, dataset version, row counts, and SHA-256 hashes of the raw downloads.
- match_overrides.json — human-reviewed crosswalk overrides.

## Crosswalk semantics

The current registry covers queue/connection records at or above 100 MW in nine
organized markets. Epoch instead tracks major physical AI-data-center sites,
including sites outside those markets, selected under-construction projects,
and campuses that may be represented by a different grid-project or phase name.

A direct queue match is therefore only recorded when the identity is defensible.
A site without a direct match is not treated as evidence that no grid request
exists. Queue MW and Epoch IT-power MW are different measurements.

Epoch data remains source-specific: Epoch's estimates are displayed and cited as
Epoch estimates and never overwrite queue-origin values.

## Provenance

Source:
https://epoch.ai/data/ai-data-centers

Field documentation:
https://epoch.ai/data/data-centers-documentation/records

Downloads:
https://epoch.ai/data/data-centers-documentation/downloads

The sync is maintained by
.github/workflows/sync_epoch_ai_data_centers.yml and
sync_epoch_ai_data_centers.py. The workflow validates that the main dataset
contains 93 sites, preserves the raw downloads, validates the dashboard's
inline JavaScript and commits only changed evidence files.

Epoch states that its data are free to use, distribute and reproduce provided
the source and authors are credited under Creative Commons Attribution 4.0.
