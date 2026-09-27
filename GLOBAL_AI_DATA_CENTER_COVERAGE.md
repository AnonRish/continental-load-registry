# Global AI Data-Center Coverage & Discovery Ledger

Updated: 2026-09-27

## What “100% captured” means here

The repository already contains **100% of the current Epoch AI AI-data-centers directory: 93 of 93 records**, accessed on 2026-09-27 from Epoch's current directory. Epoch's directory itself is not a global census: its September 2026 research update reported an estimated 44% of global AI compute coverage when its explorer had 86 sites, with materially lower coverage for China.

The purpose of this layer is therefore twofold: preserve a complete mirror of the current Epoch explorer and maintain a separate discovery queue for facilities/programs found in other public datasets so candidates can be entity-resolved before they enter the canonical site registry.

## Current Epoch coverage

- 93 / 93 current Epoch explorer records preserved.
- Epoch directory update: 2026-09-24.
- Epoch published global AI-compute coverage reference: 44% as of 2026-09-09, based on modeled capacity rather than facility count.
- China coverage reported by Epoch: roughly 9–31%.

## External discovery universes

- AI Data Center Index: 346 facilities / 64 countries on its current public index.
- Data Center Index: 702 counted campuses / 64 countries in its 2026-09-26 public data release.
- Compute Atlas: 2,228 US facilities as of 2026-09-25.

These are **discovery/comparator universes, not additive populations**. Their records overlap and have different inclusion rules.

## Current 93-site research gaps

The current normalized Epoch layer still has missing public fields for 13 addresses, 29 projects, 83 investors, 65 construction-company entries, and 30 energy-company entries. The Track 3 research queue has 984 open tasks (273 publisher-field tasks and 711 domain cells).

## Candidate discovery queue

The JSON and CSV files contain 33 externally discovered candidates/programs. They are intentionally not merged into the 93-site canonical Epoch universe until the promotion rules are satisfied. One explicit example, Meta Hyperion, is already in Epoch and is retained only as a corroborating discovery record.

## Promotion standard

A candidate becomes a canonical facility only after: (1) entity resolution; (2) a public source establishing the facility identity; (3) explicit capacity scope and date; (4) status verification; (5) overlap checks against Epoch, Data Center Index, Compute Atlas and the existing registry; and (6) preservation of source URLs and attribution.

## Sources

- Epoch AI — AI data centers: https://epoch.ai/data/ai-data-centers/directory
- Epoch AI — Global AI data-center research update: https://epoch.ai/topics/data-centers
- AI Data Center Index: https://aidatacenterindex.com/
- Data Center Index: https://datacenterindex.ai/data
- Compute Atlas: https://www.compute-atlas.com/data
