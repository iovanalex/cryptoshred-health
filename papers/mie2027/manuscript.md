# Verifying EHR Erasure Claims through Fault Injection and FHIR Export Semantics

Adina NITULESCU, Robert HEVESI, Mihaela CRISAN-VIDA and Alexandru IOVANOVICI

Politehnica University Timisoara, Faculty of Automation and Computers, Timisoara, Romania

Corresponding author: Alexandru Iovanovici, alexandru.iovanovici@upt.ro

## Abstract

Erasure should not imply clinical resolution or introduce allergy or medication records. We observed these transformations in FHIR exports from one electronic health record (EHR) prototype using synthetic data. A claim-to-observation protocol evaluated patient/visit erasure, two injected failures and paired HL7 FHIR R4 exports against policy, decryptability, persisted status, disclosure and clinical-meaning criteria. Denied cache deletion left readable data despite a receipt claiming eviction. A rejected database update left metadata inconsistent with key destruction already performed by the workflow. Visit erasure introduced two placeholder resources, including a confirmed AllergyIntolerance, and changed Condition status from active to inactive. Paired analysis separated semantic changes from baseline export defects. Three fresh deployments reproduced the deterministic observations.

Keywords: electronic health records; cryptographic erasure; fault injection; HL7 FHIR; semantic interoperability

## Introduction

An absent diagnosis may mean that it was never recorded, access is restricted or information is unavailable, rather than that the condition has resolved. Conversely, an allergy resource introduced during erasure can falsely suggest a clinically recorded allergy. These distinctions matter when clinicians interpret exchanged records.

An electronic health record (EHR) can hold encrypted records, readable temporary copies in a cache and exports shared with other services. Cryptographic erasure destroys a key needed to decrypt data [1,2]; encrypted bytes may remain, while readable cached copies need separate removal. Deletion receipts should clarify what remains and how absence is represented.

Secure-deletion research distinguishes mechanisms across storage layers [2]. Politou et al. describe the difficulty of erasure and consent withdrawal in disseminated systems [3]; GDPR Article 17 also specifies exceptions [4]. Logging guidance warns against unnecessary retention of sensitive data [5]. HL7 FHIR defines clinical resources and security labels [6,7]. Lee et al. pilot-tested consent-based FHIR segmentation and redaction [8]; Malin and Airoldi showed how linking access logs can expose sensitive information [9]. Erasure adds a distinct question: do storage effects and exported meaning remain consistent?

Our protocol checks agreement between storage, receipts and clinical representations after erasure and interruptions. Historical recovery and performance are outside scope.

## Methods

### System and scenario selection

CryptoShred Health uses Java 21/Spring Boot 3.3.4, PostgreSQL 15, Redis 7, Kafka 3.7.0 and Vault 1.13.3. Vault key-encryption keys (KEKs) wrap data-encryption keys (DEKs); Redis caches decrypted responses. We exercised the application JAR as its seeded DOCTOR role. Three isolated continuous-integration (CI) jobs ran the same deterministic sequences with fresh services, four synthetic patients and one visit each. Evaluated commit 436d4d662315e82de62df07776c449f02d26bae3 and retained evidence are available [10].

Source review traced retention, key destruction, SQL updates, cache eviction, events and receipts. S2/S3 exercised normal patient/visit paths; S1 probed retention and S5 snapshot decryptability. S4 denied Redis DEL while allowing GET, modelling permission drift. S6 rejected a patient update through a SQL trigger, modelling persistence rejection such as a constraint failure. These source-informed faults target non-transactional boundaries, not network partitions or timeouts.

### Claim-to-observation protocol

D criteria derive from the pre-existing service contract [10]; only P criteria are proposed here (Table 1). S4 tests a prior eviction commitment. S1 remains conditional: the design specifies classification, not a mandatory override gate.

Table 1. Assertions, required observations, expected outcomes and scenarios.

| Assertion | Observation | Expected outcome and basis | Scenario |
|---|---|---|---|
| Policy decision | Classification, request reason and acceptance | Explicit execution policy; if PROTECTED requires override, reject an unexplained request (P) | S1 |
| Decryption unavailable | Unwrap same snapshot DEK before/after; inspect KEK | Initial unwrap succeeds, subsequent unwrap fails and KEK is absent (D) | S5 |
| Persisted status truthful | SQL row, key state and API after failure | Completed or durable pending state agrees with irreversible effects (P); normal scope is respected (D) | S2, S3, S6 |
| Disclosure and receipt agree | Read named cache directly and compare API/receipt | Claimed eviction requires absent cache entry (D); failure must not be reported as success (P) | S2, S4 |
| Clinical meaning preserved | Resource types, fields and clinical codes | No clinical assertion or status change solely from erasure (F) | S2, S3 |

Table note. D: prior contract; F: FHIR semantics; P: proposed criterion. Clinical-meaning checks use the S2 patient export and S3 paired visit exports.

S2 checked API firstName, shredded status and Redis key absence. Post-hoc export checks added family name, birthDate and identifier retention, not pre-specified tests. S3 checked visit status and preservation of the patient's name. S5 compared the snapshot's wrapped DEK, Vault response and SHA-256 before/after erasure. In S6, the workflow itself destroyed the KEK before SQL persistence failed; SQL inspection preceded a later GET. Fault controls were removed after each sequence.

Receipts contain scope, identifiers, requester, retention reason, timestamp, per-layer claims, an audit hash and Merkle inclusion data, with RSA and ML-DSA signatures. Source inspection traced receipt construction, transaction boundaries and the canonical signed fields; signature strength was not evaluated.

### Export assessment and residual-store scope

Each deployment yielded patient-after and paired visit-before/after exports. HAPI FHIR 8.8.2 assessed unmodified JSON against base R4 [11], without terminology validation or UK Core packages. We distinguished baseline diagnostics from added occurrences and inspected clinical meaning against Condition definitions [6]. Scripts and input hashes are retained [10].

A source audit covered Kafka event builders, DTO fields and the publisher. It distinguishes encrypted payloads from readable event metadata; topic consumption was not performed. PostgreSQL write-ahead logs and historical backups were excluded because the protocol concerns current workflow consistency rather than storage-forensic sanitisation or recovery. The snapshot check covers one decryption path only.

## Results

### Erasure-induced clinical representations

Before visit erasure, the Bundle contained Patient, Encounter and Condition. Afterwards it also contained AllergyIntolerance and MedicationStatement generated from non-empty [SHREDDED] placeholders. The new allergy carried verificationStatus=confirmed and clinicalStatus=inactive; the medication status was unknown. The existing Condition changed from active to inactive. No clinical update occurred between exports. These are unsupported clinical representations.

The REDACTED marker appeared in meta.tag rather than meta.security. S2's retained Patient export contained redacted given and family names, omitted birthDate and retained the synthetic patient identifier. These observations recurred in all three executions; the retained identifier precludes complete anonymisation.

### Paired structural diagnostics

Table 2 compares paired visit exports. Baseline errors concerned timezones, an invalid OID, relative fullUrl values and total in a collection Bundle. New resources added occurrences of existing defects: two relative-fullUrl errors, two narrative warnings and two unavailable-profile warnings. The semantic findings arise from export comparison, not diagnostic counts.

Table 2. Paired visit exports per execution; the same counts recurred three times.

| Measure | Before | After | Erasure-associated addition |
|---|---|---|---|
| Resources | 3 | 5 | AllergyIntolerance and MedicationStatement |
| Errors | 7 | 9 | 2 relative-fullUrl occurrences |
| Warnings | 6 | 10 | 2 narratives and 2 unavailable profiles |

### Storage, policy and receipt consistency

S2 redacted API firstName, set shredded=true and removed the named cache entry. S3 reported the visit shredded while preserving patient demographics. In S5, the retained encrypted snapshot was byte-identical; Vault unwrap changed from HTTP 200 to 400 and KEK lookup returned 404.

Under S4, Redis retained the synthetic name after DEL was denied, while the API suppressed it. The receipt asserted ALL_PATIENT_CACHES_EVICTED, contradicting the D eviction commitment. Source inspection explains the mismatch: eviction exceptions are caught and logged, and the claim is not conditioned on the DEL outcome. The receipt is constructed after eviction invocation and asynchronous Kafka submission, before SQL commit.

Source inspection also found that signatures cover the identifier, timestamp, audit hash and Merkle root, but not layerStatus. Thus the false per-layer eviction claim was outside the authenticated fields, despite accompanying signatures.

In S6 the request returned HTTP 500, but key destruction survived SQL rollback. The inspected row retained shredded=false and ciphertext, whereas the later GET reported shredded=true without the original name. This failed the persisted-status criterion: irreversible key destruction preceded transaction completion.

S1 accepted a PROTECTED patient without an override and supplied STANDARD_REQUEST in its receipt. Source review confirms permitted behaviour with an unspecified execution gate, not a demonstrated blocking-rule breach or legal conclusion.

Kafka source review found creation events with encrypted payloads and readable identifiers; erasure events retained patientId, eventType, key reference and timestamp. Those metadata remain outside key-based payload erasure.

## Discussion

Exporters should suppress placeholder-triggered resources rather than imply a new allergy, medication or disease transition. Where policy permits redaction markers, use v3 ObservationValue REDACTED in meta.security with agreed consumer handling [7,12]. A masked data-absent-reason can describe withheld elements where permitted [13]. Condition con-3 recommends clinicalStatus for problem-list items; con-5 prohibits it when verificationStatus is entered-in-error [6]. Neither constraint justifies inventing inactivity or falsely declaring a diagnosis erroneous. Resource omission or a constrained redacted representation requires an explicit exchange policy.

S4 requires distinguishing attempted from confirmed eviction. For S6, a candidate outbox/saga-style workflow would commit intent, destroy keys idempotently and persist completion, with retry or escalation. This remedy remains untested. Receipt authentication cannot establish the truth of unobserved effects.

Reuse requires enumerating stores, defining effects and criteria, assigning observers and preserving paired outputs. Deployment policy must address retained Kafka identifiers and audit metadata.

Limitations are one prototype, one role, small fixtures and source-informed deterministic faults. Repetitions demonstrate repeatability, not robustness or independent replication. Demographic checks cover selected API fields and retained FHIR outputs; S6 SQL was not re-queried after GET. Development-mode Vault, one broker, unconsumed Kafka topics and excluded WAL/historical backups bound storage claims. Validation excludes terminology and UK Core conformance. No clinical-user study, patient-harm assessment or legal-compliance determination was performed.

## Conclusions

A claim-to-observation protocol exposed unsupported clinical resources and status transitions after erasure, a cache-eviction claim contradicted by readable data, and metadata inconsistent with prior key destruction. Paired analysis isolated erasure effects from baseline export defects. Verifiable erasure workflows require distinct evidence for policy, storage effects, completion status, disclosure and clinical meaning.

## References

[1] Chandramouli R, Hibbard E. Guidelines for Media Sanitization. NIST SP 800-88 Rev. 2. September 2025. doi:10.6028/NIST.SP.800-88r2.

[2] Reardon J, Basin D, Capkun S. SoK: Secure Data Deletion. In: IEEE Symposium on Security and Privacy. 2013. p. 301-315. doi:10.1109/SP.2013.28.

[3] Politou E, Alepis E, Patsakis C. Forgetting personal data and revoking consent under the GDPR: Challenges and proposed solutions. J Cybersecur. 2018;4(1):tyy001. doi:10.1093/cybsec/tyy001.

[4] European Parliament, Council of the European Union. Regulation (EU) 2016/679. Off J Eur Union. 2016;L119:1-88. Article 17.

[5] OWASP Foundation. Logging Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html. Accessed 15 October 2026.

[6] HL7 International. FHIR R4 Condition Definitions. 2019. https://hl7.org/fhir/R4/condition-definitions.html.

[7] HL7 International. FHIR R4 Security Labels. 2019. https://hl7.org/fhir/R4/security-labels.html.

[8] Lee P, Mendoza D, Kaiser M, Lott E, Singh G, Grando A. FHIR Granular Sensitive Data Segmentation. Appl Clin Inform. 2025;16(1):156-166. doi:10.1055/a-2466-4371.

[9] Malin B, Airoldi E. Confidentiality preserving audits of electronic medical record access. Stud Health Technol Inform. 2007;129(Pt 1):320-324.

[10] CryptoShred Health. MIE 2027 evaluation source and retained evidence. 2026. https://github.com/iovanalex/cryptoshred-health/tree/paper/mie2027-evaluation.

[11] HAPI FHIR. Instance Validator. https://hapifhir.io/hapi-fhir/docs/validation/instance_validator.html. Accessed 15 October 2026.

[12] HL7 International. FHIR R4 HL7 v3 Code System ObservationValue. 2019. https://hl7.org/fhir/R4/v3/ObservationValue/cs.html.

[13] HL7 International. FHIR R4 DataAbsentReason. 2019. https://hl7.org/fhir/R4/codesystem-data-absent-reason.html.
