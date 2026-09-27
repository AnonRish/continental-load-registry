# Track 3 Research Workflows

This is the operational research layer for the **effective unresolved publisher fields** and **open Track 3 domain cells** in the 93-site canonical universe.

## One-task workflow

1. Select one task ID from the Research Operations Console or the CSV queue.
2. Run the generated site-specific search links and named source sequence.
3. Capture the exact document, filing, permit, scene, or record; its URL; locator; dates; site linkage; and supported value/observation.
4. Reject company-wide, regional, nearby, generic, inferred, or otherwise non-site-specific claims.
5. For material claims, obtain independent corroboration and record what agrees or disagrees.
6. Classify the result explicitly: FOUND, PUBLIC_LEAD_REVIEW_REQUIRED, NO_PUBLIC_RECORD, SOURCE_UNAVAILABLE, DUPLICATE_OF_EXISTING_SOURCE, or CONFLICT_NEEDS_REVIEW.
7. Submit using the research submission schema. Canonical builders remain the state gate.

## Queue accounting

The generated queue has exactly one task per effective unresolved publisher field and exactly one task per open Track 3 domain cell. The build script asserts these counts against the canonical sweep before writing outputs.

## Sources

The playbooks prioritize official project/developer records, utility and regulator records, municipal/county records, environmental and permitting records, company disclosures, Epoch site-level records, and reputable independent reporting. Remote-sensing tasks use the public Copernicus and USGS source families already cataloged in the registry.

## Important evidence rules

- A public lead is not canonical evidence until source review and ingestion.
- Missing publication is not a publication date.
- Queue MW, utility service capacity, contracted demand, generation capacity, chip TDP, and measured load are different measurements.
- A source mirror or syndicated copy is not independent corroboration.
- A no-public-record outcome is a documented research result, not evidence that the infrastructure or relationship does not exist.

## Rebuild

Run:

python build_track3_research_backlog.py

The daily GitHub Actions workflow rebuilds the queue whenever the canonical sweep or workflow definitions change.
