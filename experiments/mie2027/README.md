# MIE 2027 evaluation workspace

This directory isolates the evidence used for the MIE 2027 conference paper from
the performance paper and from the recovery-safe cryptographic-erasure work
reserved for the journal extension.

## Evaluation question

The conference study asks whether an erasure request is reflected consistently
in the application's interoperable record state, including retention metadata,
patient- and visit-level redaction, cache handling, audit evidence, and FHIR R4
export behaviour.

## Evidence levels

The evaluation deliberately distinguishes three levels of evidence:

1. **Component evidence** uses JUnit with mocked external services. It checks
   workflow decisions and output structure, but does not demonstrate distributed
   end-to-end behaviour.
2. **FHIR parser evidence** uses the independent HAPI FHIR R4 model and strict
   parser against both active and crypto-shredded exports. This establishes R4
   syntax/model compatibility, but must not be described as formal UK Core
   profile conformance.
3. **End-to-end scenario evidence** will execute the application against
   PostgreSQL, Redis, Kafka, and Vault, with controlled failure injection.

Levels 1 and 2 are automated by the current workflow. Full UK Core profile
validation and level 3 remain explicit follow-up gates, so a passing smoke test
cannot be mistaken for a completed end-to-end MIE evaluation.

## Initial scenario map

The machine-readable mapping is in `scenario-matrix.csv`.

| ID | Scenario | Initial evidence | Target evidence |
|---|---|---|---|
| S1 | Retention-protected erasure request | Component | End-to-end |
| S2 | Patient-level erasure and redacted FHIR state | Component + strict R4 parser | UK Core validator + end-to-end |
| S3 | Visit-level erasure and retained patient state | Component + strict R4 parser | UK Core validator + end-to-end |
| S4 | Redis eviction failure or stale cache | None | Failure injection |
| S5 | WORM snapshot and post-erasure unreadability | Component | End-to-end |
| S6 | Partial failure across Vault, SQL, Redis, and Kafka | None | Failure injection |

## Running the current smoke suite

With Java 21 and Maven available:

```bash
cd backend
../experiments/mie2027/run-component-evidence.sh
```

GitHub Actions runs the same command on branch
`paper/mie2027-evaluation`. It uploads raw Surefire XML, the generated active
and shredded FHIR R4 Bundles, JSON and CSV summaries, provenance metadata, and
SHA-256 checksums as a 90-day artifact.

## Reproducibility rules

- Keep raw outputs; derive paper tables and figures from them.
- Record the exact Git commit and workflow run identifier.
- Keep component, validator, and end-to-end results in separate directories.
- Never report hosted-runner timing as system performance.
- Treat a mocked dependency as unavailable evidence for cross-service failure
  semantics, not as a successful end-to-end test.

