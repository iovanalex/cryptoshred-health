# MIE 2027: live erasure workflow findings

## Scope and traceability

This is an engineering evaluation of the current prototype using synthetic
records. It is not a clinical evaluation, legal compliance assessment,
performance benchmark, or exhaustive fault-tolerance study.

Verified evidence run:
https://github.com/iovanalex/cryptoshred-health/actions/runs/38671560141

Evaluated commit: `af7a9116f17c39b2a17541ae5922176a080b8202`.
The downloaded artifact's complete SHA-256 manifest was verified successfully.
The component suite also completed successfully for the same commit:
https://github.com/iovanalex/cryptoshred-health/actions/runs/38671560037

The workflow builds and runs the production Spring Boot JAR with PostgreSQL 15,
Redis 7, Kafka 3.7.0, and Vault 1.13.3. Vault runs as a single development-mode
instance; this experiment does not test HA or restored historical snapshots.
Requests go through authenticated HTTP endpoints. No application services or
repositories are mocked in these scenarios.

## Observed results

| Scenario | Observation | Interpretation |
|---|---|---|
| S1: retention-protected patient | API reports `PROTECTED` before erasure; deletion succeeds and the receipt still reports `PROTECTED`. | Retention classification is recorded but is not an enforced deletion gate in this path. |
| S2: patient erasure | The demographic API returns `[SHREDDED]`; the normal Redis entry is absent. A post-erasure FHIR Bundle is captured. | Normal patient-level redaction and cache eviction work for the tested fixture. |
| S3: visit erasure | The visit response is shredded while the patient's original synthetic name remains available. FHIR Bundles are captured before and after. | The tested visit-level operation preserves patient demographics. |
| S4: Redis refuses DEL | Redis retains the synthetic name, but the patient API returns redacted data. The receipt reports `ALL_PATIENT_CACHES_EVICTED`. | API redaction, residual plaintext, and receipt accuracy are distinct properties. The receipt overstates the observed cache outcome. |
| S5: pre-erasure WORM snapshot | Vault unwrap succeeds before erasure (HTTP 200); afterwards the key lookup is 404 and the same unwrap request returns 400. Snapshot bytes have the same SHA-256 fingerprint. | The saved encrypted visit loses its tested key-unwrapping path without modifying the snapshot. This does not certify the storage medium as WORM. |
| S6: SQL update fails after Vault deletion | A trigger injects a SQL failure. The erasure request returns HTTP 500. The SQL row retains `shredded=false` and its ciphertext, while Vault returns 404 for its KEK. A subsequent patient GET returns a shredded response without the original name. | SQL rollback cannot reverse the external key destruction; persisted SQL state, key availability, and the API representation diverge. |

The S4 fault is a Redis ACL denying `DEL`, with `GET` still allowed. The S6
fault is a database trigger restricted to one named synthetic patient. Both
are removed in `finally` blocks. These controls provide deterministic fault
injection without modifying the application's erasure implementation.

## What a successful workflow means

The CI job is successful because the scenarios execute and the observation
checks hold. It does **not** mean the application satisfies every erasure
requirement. S1, S4, and S6 deliberately expose limitations of the current
implementation.

The results currently cover one fixture for each scenario in a disposable CI
environment. They do not establish failure probabilities, timing bounds,
coverage of all clinical resources, or the behaviour of every possible
interleaving. Kafka runs as a real dependency, but broker persistence and
consumer delivery are not independently asserted by this suite.

## FHIR evidence boundaries

The separate component suite passes 20 existing tests and parses its active
and shredded fixtures with the strict HAPI R4 parser. A subsequent evaluation at
commit `436d4d662315e82de62df07776c449f02d26bae3` independently assessed live
exports using the HAPI FHIR 8.8.2 instance validator across three deployments.
All nine exports produced base R4 structure/invariant errors: 4 per patient-after
Bundle, 7 per visit-before Bundle and 9 per visit-after Bundle. Terminology checks
were disabled and UK Core packages were not loaded. Retained evidence and the
empirical manuscript are under `papers/mie2027`.
Run: https://github.com/iovanalex/cryptoshred-health/actions/runs/38672097976

## Manuscript implications

The defensible conference contribution is a scenario-based analysis of the
relationship between an erasure request, its observable record state, and
the claims in the resulting receipt. The findings support explicit treatment
of retention decisions, residual cache plaintext, partial completion, and
interoperability exports.

Recovery after restoring historical KMS state, tombstone reconciliation,
scalability, and post-quantum proof evaluation remain outside this experiment.
They can retain their role in the journal study.

Future corrections to application behaviour should be evaluated separately
from this baseline, with an explicit before/after comparison. Silent repairs
would obscure the evidence explaining the operational requirements.
