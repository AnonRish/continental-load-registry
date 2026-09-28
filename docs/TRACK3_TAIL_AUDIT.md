
# Track 3 tail audit

The AI 2040 Plan A scenario proposes exhaustive auditing above a threshold and
random sampling of the remaining small-owner tail, with sampled units traced
through resales until they reach physically inspected inventory or fail.

This repository now has a reproducible implementation of the tail sampling and
account-reconciliation layer. It does not claim that the public registry has a
closed global population or authoritative serial-level records.

The sampling frame must be frozen before the seed is revealed to the party being
audited. The sample is weighted by delivered compute so a large tail recipient
cannot hide behind being one legal entity among many.

A field implementation should replace the example data structures with:
vendor-sales records, resale/transfer records, inventory records, decommissioning
records, stable serial identifiers, and independent physical inspection evidence.
