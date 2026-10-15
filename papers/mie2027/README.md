# MIE 2027 empirical manuscript

Title: **Verifying EHR Erasure Claims through Fault Injection and FHIR Export Semantics**

Authors: Adina Nitulescu, Robert Hevesi, Mihaela Crisan-Vida and Alexandru Iovanovici.

`manuscript.md` is the editable source. `build_manuscript.py` renders it to Word
using the official IOS Press book-article template. The Word document has been
rendered and visually checked against the five-page limit. The earlier
documentary-analysis manuscript remains a separate fallback.

## Evidence

- Evaluated commit: `436d4d662315e82de62df07776c449f02d26bae3`.
- Run: https://github.com/iovanalex/cryptoshred-health/actions/runs/38672097976
- Three isolated hosted runners, each with fresh services and data.
- Artifacts: `11944489680` (1), `11943939682` (2), `11944089755` (3).
- All downloaded artifacts passed their complete SHA-256 manifest checks.
- Six scenario concerns execute in four groups, not six independent fixtures.
- All Boolean scenario observations match across repetitions.
- Three export positions recur across repetitions; paired visit exports separate baseline defects from additional occurrences.
- Errors per export: 4 (patient after), 7 (visit before), 9 (visit after).

`evidence/repetition-*` retains observations, live FHIR exports, validator
summaries, OperationOutcome files, provenance, receipts, SQL outcomes and image
identifiers. Complete logs remain in the run artifacts with 90-day retention. Committed
evidence preserves the manuscript results after artifact expiry.

## Build

With python-docx installed and the official IOS Press Word template:

```bash
python build_manuscript.py --template /path/to/IOS-template.docx --output manuscript.docx
```

Review pagination after rebuilding because fonts and layout engines can affect it.

## Submission boundary

The paper evaluates workflow consistency and residual representations. It does
not republish throughput, historical recovery, tombstone reconciliation or
post-quantum proof evaluation. FHIR validation excludes terminology and UK Core
packages. No UK Core conformance, clinical benefit or legal compliance is claimed.
 Author review is required before submission.

## Major revision analysis

Run `python papers/mie2027/analyse_retained_evidence.py` from the repository root.
It verifies paired resource/diagnostic changes and additional Patient FHIR
demographic observations, retaining input hashes in `evidence/paired-analysis.json`.
This is post-hoc analysis of existing live evidence, not a new deployment. Kafka
findings are source observations, not consumed-topic measurements.
See `response-to-review.md` for changes and remaining scope limits.
