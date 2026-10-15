# Verifying EHR Erasure Claims through Fault Injection and FHIR Export Semantics

Adina NITULESCU, Robert HEVESI, Mihaela CRISAN-VIDA and Alexandru IOVANOVICI

Politehnica University Timisoara, Faculty of Automation and Computers, Timisoara, Romania

Corresponding author: Alexandru Iovanovici, alexandru.iovanovici@upt.ro

## Abstract

An erased diagnosis should not become an inactive condition, nor should erasure introduce an allergy or medication record. We observed both transformations in FHIR exports from an electronic health record (EHR) prototype. We formalised a claim-to-observation evaluation protocol and applied it to synthetic patient and visit erasure, two injected failures and paired HL7 FHIR R4 exports. Five assertions were linked to separate observations and explicit criteria: policy decisions, decryption capability, persisted status, disclosure suppression and clinical representation. Denied cache deletion left readable data despite a receipt claiming eviction. A rejected database update left metadata inconsistent with key destruction already performed by the workflow. Visit erasure introduced two placeholder resources, including a confirmed AllergyIntolerance, and changed Condition status from active to inactive. Paired analysis distinguished these semantic changes from pre-existing structural export defects. Repeating deterministic scenarios in three fresh deployments reproduced the observations. The protocol makes erasure assurances inspectable across storage, receipts and exchanged clinical representations.

Keywords: electronic health records; cryptographic erasure; fault injection; HL7 FHIR; semantic interoperability

## Introduction

For a clinician, an absent diagnosis may mean that it was never recorded, access is restricted or information is unavailable. None means that the condition has resolved. Similarly, an allergy resource introduced during erasure can imply previously unrecorded clinical information. Systems must distinguish changes in information availability from changes in a patient's condition.

An electronic health record (EHR) can hold encrypted records, readable temporary copies in a cache and exports shared with other services. Cryptographic erasure destroys a key needed to decrypt data [1,2]; encrypted bytes may remain, while readable cached copies need separate removal. A deletion receipt reports what the system claims to have completed. Clinicians and information-governance staff therefore need to know what was removed, what remains and how absence is represented.

Secure-deletion research distinguishes mechanisms across storage layers [2]. Politou et al. describe the difficulty of erasure and consent withdrawal in disseminated systems [3]; GDPR Article 17 also specifies exceptions [4]. Logging guidance warns against unnecessary retention of sensitive data [5]. HL7 FHIR defines clinical resources and security labels for exchange [6,7]. These perspectives motivate checking storage effects and the meaning of resulting exports together.

We present a claim-to-observation protocol for an EHR prototype, relating each assertion to an observation and criterion. We examine current erasure requests and interruptions, rather than historical backup restoration or performance. The central question is whether storage, receipts and clinical representations agree after erasure.

## Methods

### System and scenario selection

CryptoShred Health uses Java 21/Spring Boot 3.3.4, PostgreSQL 15, Redis 7, Kafka 3.7.0 and Vault 1.13.3. Vault key-encryption keys (KEKs) wrap data-encryption keys (DEKs); Redis caches decrypted responses. We exercised the application JAR as its seeded DOCTOR role. Three isolated hosted jobs ran the same deterministic sequences with fresh services, four synthetic patients and one visit each. Evaluated commit 436d4d662315e82de62df07776c449f02d26bae3 and retained evidence are available [8].

Source review traced retention, key destruction, SQL updates, cache eviction, events and receipts. S2/S3 exercised normal patient/visit paths; S1 probed retention and S5 snapshot decryptability. S4 denied Redis DEL while allowing GET, modelling permission drift. S6 rejected a patient update through a SQL trigger, modelling persistence rejection such as a constraint failure. These source-informed faults target non-transactional boundaries, not network partitions or timeouts.

### Claim-to-observation protocol

Table 1 retrospectively formalises the evaluation: D denotes a service-contract effect [8], F a FHIR semantic requirement and P a proposed operational criterion. S1 is conditional: the design specifies classification, not a mandatory override gate. Observations are assessed against these criteria; unresolved requirements remain explicit.

Table 1. Assertions, required observations, expected outcomes and scenarios.

| Assertion | Observation | Expected outcome and basis | Scenario |
|---|---|---|---|
| Policy decision | Classification, request reason and acceptance | Explicit execution policy; if PROTECTED requires override, reject an unexplained request (P) | S1 |
| Decryption unavailable | Unwrap same snapshot DEK before/after; inspect KEK | Initial unwrap succeeds, subsequent unwrap fails and KEK is absent (D) | S5 |
| Persisted status truthful | SQL row, key state and API after failure | Completed or durable pending state agrees with irreversible effects (P); normal scope is respected (D) | S2, S3, S6 |
| Disclosure and receipt agree | Read named cache directly and compare API/receipt | Claimed eviction requires absent cache entry (D); failure must not be reported as success (P) | S2, S4 |
| Clinical meaning preserved | Paired resource types, fields and clinical codes | No new clinical assertion or status change solely from erasure (F) | S2, S3 |

For S2 we checked API firstName and shredded status plus Redis key absence. Subsequent analysis of retained patient FHIR output additionally checked family name, birthDate and identifier retention. S3 checked visit status and preservation of the patient's name. S5 compared the snapshot's wrapped DEK, Vault response and SHA-256 before/after erasure. In S6, the workflow itself destroyed the KEK before SQL persistence failed; SQL inspection preceded a later GET. Fault controls were removed after each sequence.

Receipts contain scope, identifiers, requester, retention reason, timestamp, per-layer claims, an audit hash and Merkle inclusion data. RSA and ML-DSA signatures cover an identifier, timestamp, audit hash and Merkle root, not the complete JSON receipt. The service constructs the receipt after cache-eviction invocation and asynchronous Kafka submission, before the surrounding SQL transaction commits. Cache errors are caught and logged. We compare claims with effects; signature strength is outside this evaluation.

### Export assessment and residual-store scope

Each deployment yielded three export positions: patient after erasure and a paired visit before/after. HAPI FHIR 8.8.2 assessed unmodified JSON against base R4 definitions [9]. Terminology validation was disabled and UK Core packages were unavailable. We separated existing diagnostic classes from added occurrences on newly introduced resources, then inspected clinical meaning against Condition definitions [6]. Analysis scripts and input hashes are retained [8].

A source audit covered Kafka event builders, DTO fields and the publisher. It distinguishes encrypted payloads from readable event metadata; topic consumption was not performed. PostgreSQL write-ahead logs and historical backups were excluded because the protocol concerns current workflow consistency rather than storage-forensic sanitisation or recovery. The snapshot check covers one decryption path only.

## Results

### Erasure-induced clinical representations

Before visit erasure, the Bundle contained Patient, Encounter and Condition. Afterwards it also contained AllergyIntolerance and MedicationStatement generated from non-empty [SHREDDED] placeholders. The new allergy carried verificationStatus=confirmed and clinicalStatus=inactive; the medication status was unknown. The existing Condition changed from active to inactive. No clinical update occurred between exports. These changes create unsupported clinical representations, rather than merely signalling unavailable information.

The REDACTED marker appeared in meta.tag rather than meta.security. S2's retained Patient export contained redacted given and family names, omitted birthDate and retained the synthetic patient identifier. Identifier retention was therefore explicit, not evidence of complete anonymisation. All these observations recurred in the three executions.

### Paired structural diagnostics

Table 2 reports the paired visit comparison, not nine independent validation samples. Seven errors were already present before erasure: timezone/instant defects, an invalid identifier OID, relative fullUrl values and use of total in a collection Bundle. After erasure, two additional relative-fullUrl errors occurred on the new resources. Four additional warnings comprised two missing narratives and two unresolved UK Core profiles. Thus erasure increased occurrences of existing defect classes; it did not introduce new structural error classes. Semantic changes were established by comparison, independently of these counts.

Table 2. Paired visit exports per execution; the same counts recurred three times.

| Measure | Before | After | Erasure-associated addition |
|---|---|---|---|
| Resources | 3 | 5 | AllergyIntolerance and MedicationStatement |
| Errors | 7 | 9 | 2 relative-fullUrl occurrences |
| Warnings | 6 | 10 | 2 narratives and 2 unavailable profiles |

### Storage, policy and receipt consistency

S2 redacted API firstName, set shredded=true and removed the named cache entry. S3 reported the visit shredded while preserving patient demographics. In S5, the retained encrypted snapshot was byte-identical; Vault unwrap changed from HTTP 200 to 400 and KEK lookup returned 404.

Under S4, Redis retained the synthetic name after DEL was denied, while the patient API suppressed it. The receipt nevertheless asserted ALL_PATIENT_CACHES_EVICTED. This failed the disclosure/receipt criterion: API suppression and removal of readable cached data diverged.

In S6 the request returned HTTP 500, but external key destruction survived SQL rollback. The inspected row retained shredded=false and ciphertext, whereas the later GET reported shredded=true without the original name. This failed the persisted-status criterion. The failure arose from an irreversible action preceding transaction completion.

S1 accepted a PROTECTED patient without an override and supplied STANDARD_REQUEST in its receipt. Source review confirmed this is permitted behaviour. The result exposes an unspecified execution gate, not a demonstrated breach of a documented blocking rule or a legal conclusion. Kafka source review found creation events with encrypted payloads and readable identifiers; erasure events retained patientId, eventType, key reference and timestamp. Those metadata remain outside key-based payload erasure.

## Discussion

The strongest clinical implication is that removing information must not manufacture an allergy, medication record or disease transition. Exporters should suppress placeholder-triggered resources. Where disclosure policy permits indicating redaction, REDACTED from the v3 ObservationValue system belongs in meta.security, with agreed consumer handling [7,10]. A masked data-absent-reason can describe withheld elements where permitted [11]. Condition con-3 recommends clinicalStatus for problem-list items; con-5 prohibits it when verificationStatus is entered-in-error [6]. Neither constraint justifies inventing inactivity or falsely declaring a diagnosis erroneous. Resource omission or a constrained redacted representation requires an explicit exchange policy.

Operationally, S4 requires reporting confirmed eviction separately from attempted eviction. S6 requires durable intent and recoverable completion: commit a pending action, execute key destruction idempotently and persist completion, with retry or escalation for interrupted steps. An outbox/saga-style workflow is a candidate design, not a remedy tested here. Moving a success message alone cannot solve the ordering problem. Receipt authentication likewise cannot prove storage effects that were not observed; in this implementation per-layer JSON claims are also outside the signed canonical fields.

The protocol can be reused by enumerating stores, stating each effect, assigning a separate observer and criterion, and preserving paired outputs. Policy requirements must be supplied by the deployment, not inferred from a label. Kafka identifiers and audit metadata require their own retention policy. Key destruction addresses encrypted payload access, not every representation or retained link.

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

[8] CryptoShred Health. MIE 2027 evaluation source and retained evidence. 2026. https://github.com/iovanalex/cryptoshred-health/tree/paper/mie2027-evaluation.

[9] HAPI FHIR. Instance Validator. https://hapifhir.io/hapi-fhir/docs/validation/instance_validator.html. Accessed 15 October 2026.

[10] HL7 International. FHIR R4 HL7 v3 Code System ObservationValue. 2019. https://hl7.org/fhir/R4/v3/ObservationValue/cs.html.

[11] HL7 International. FHIR R4 DataAbsentReason. 2019. https://hl7.org/fhir/R4/codesystem-data-absent-reason.html.
