# MIE 2027 empirical manuscript

Title: **Erasure Workflows and Residual Record State in a Distributed EHR**

Authors: Robert Hevesi and Alexandru Iovanovici.

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
- All nine unmodified live FHIR Bundles produce base R4 validation errors.
- Errors per export: 4 (patient after), 7 (visit before), 9 (visit after).

`evidence/repetition-*` retains observations, live FHIR exports, validator
summaries, OperationOutcome files, provenance and image identifiers. Complete
logs and receipts remain in the run artifacts with 90-day retention. Committed
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
Update accepted-manuscript references when final proceedings metadata is
available. Author review is required before submission.
