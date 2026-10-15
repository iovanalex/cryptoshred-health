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
3. **End-to-end scenario evidence** executes the application against
   PostgreSQL, Redis, Kafka, and Vault, with controlled failure injection.

The evidence smoke workflow covers levels 1 and 2. A separate live workflow
builds the production JAR and calls authenticated HTTP endpoints with real
PostgreSQL, Redis, Kafka, and a single development-mode Vault instance. It uses
only synthetic data and fresh infrastructure on a hosted runner. It does not
evaluate Vault HA, backup recovery, Kafka delivery guarantees, or UK Core
profile conformance.

## Live scenarios

`live-scenarios.py` runs S1/S2 (patient erasure and observed retention status),
S3/S5 (visit erasure and a pre-erasure WORM snapshot), S4 (Redis ACL denies DEL),
and S6 (a PostgreSQL trigger rejects the patient update after Vault deletion).
All fault changes are confined to the disposable CI stack. Each fault is
removed in a finally block. No application code is altered to inject faults.

For WORM, the runner confirms that Vault can unwrap the saved DEK before
erasure, the KEK is absent afterwards, the same unwrap request then fails,
and the snapshot file's SHA-256 fingerprint remains unchanged. This is
functional cryptographic-erasure evidence, not certification of WORM storage.

For SQL failure, the runner checks the independently observable SQL row and
Vault key state. It deliberately does not repair the inconsistency being
measured. Redis results separately record residual plaintext, API redaction,
and the cache status asserted in the deletion proof.

An execution marked `completed` means the scenario ran and its observation
checks passed. It does not mean that the application meets the intended
erasure policy. In particular, retention enforcement and accurate cache
receipt claims are research outcomes, not assumed test preconditions.

Artifacts contain JSON observations, proof receipts, FHIR exports, a captured
backend log, service logs, provenance, and checksums. Authentication tokens
are kept in memory and not included in the scenario outputs. The backend log
is copied to a stable file before checksums are generated.

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

