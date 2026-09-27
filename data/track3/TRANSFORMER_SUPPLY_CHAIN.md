# Transformer supply-chain evidence

This layer is intentionally conservative.

The transformer_supply_chain_events.json ledger contains only source-backed records. It currently retains 2 records for Meta Hyperion: one planned MISO transformer specification and one Entergy-reported transformer transport event. Planned specifications are not installation evidence, and the transport record intentionally leaves unknown manufacturer/rating/date fields null.

The same file contains a 93-site target queue, with per-site search queries and required event fields.  Each target provides the required event fields and source families/search terms to investigate:

- utility commission and regulatory filings
- serving-utility capital/procurement records
- environmental and permitting records
- municipal construction records
- company/SEC disclosures
- manufacturer/EPC project announcements

A target is not an event. Missing events are not evidence that a transformer is absent. Source-backed events should preserve the original source URL, observed date/date precision, event type and only fields actually supported by the source.