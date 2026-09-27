## What changed

<!-- Describe the evidence, code, or documentation change in concrete terms. -->

### Evidence / provenance
- [ ] I identified the exact source URL or retained artifact.
- [ ] I recorded the observation/capture date where applicable.
- [ ] I preserved the raw publisher value and separated any normalized value.
- [ ] I did not convert a missing public record into an absence claim.
- [ ] I kept unlike MW measurements separate.

### Track 3 state
- [ ] I used the canonical Track 3 schema in data/track3_evidence_schema.json.
- [ ] I preserved the distinction between discovery lead, evidence, derived observation, and unknown.
- [ ] For physical evidence, I included scene/record identifiers, source URL, date, method, and quality metadata.
- [ ] For a correction, I identified the prior evidence record and explain the superseding evidence.

### Reproducibility
- [ ] I added or updated the appropriate manifest.
- [ ] I added/updated self-tests or validation where the code path changed.
- [ ] Generated artifacts were produced from a documented command/workflow.
- [ ] I did not commit secrets, private contact information, or unsupported conclusions.

### Checks run
<!-- Replace this line with exact commands and results. -->
- python validate_track3_ledger.py
- python validate_physical_provenance.py

### Reviewer notes
<!-- Explain any intentional limitations, unresolved ambiguity, or non-additive accounting. -->