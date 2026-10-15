# Erasure Workflows and Residual Record State in a Distributed EHR

Robert HEVESI and Alexandru IOVANOVICI

Politehnica University Timisoara, Faculty of Automation and Computers, Timisoara, Romania

Corresponding author: Alexandru Iovanovici, alexandru.iovanovici@upt.ro

## Abstract

Removing access to a medical record does not explain what remains in storage or what an exported diagnosis means. We evaluated these differences after cryptographic erasure in CryptoShred Health using synthetic records, live services, two injected faults and three fresh deployments. We compared policy metadata, storage, application responses and deletion receipts, and assessed exports against HL7 FHIR R4. Normal erasure redacted the tested name and disabled the tested snapshot decryption path. However, requests classified PROTECTED proceeded without an explicit override; denied cache eviction left plaintext despite a receipt claiming eviction; and failed database persistence left divergent states. All nine exported Bundles produced validation errors; an erasure-induced clinical-status change lacked clinical justification. The contribution is a reproducible protocol separating policy decisions, storage effects, disclosure and clinical representation. Results concern one prototype and do not establish comprehensive erasure, clinical effectiveness or legal compliance.

Keywords: electronic health records; cryptographic erasure; data governance; fault injection; HL7 FHIR; semantic interoperability

## Introduction

For clinicians, a missing diagnosis can have several meanings: the condition was never recorded, the information has been restricted, or the record is temporarily unavailable. Erasure introduces another possibility: previously recorded information can no longer be recovered. These states should not be confused with a clinical judgement that the condition has resolved. Understanding what remains visible after erasure matters when interpreting a patient's record or exchanging information with another service.

An electronic health record (EHR) is more than a single database entry. This prototype also holds temporary decrypted copies in a cache to accelerate access, encrypted visit snapshots and exports for exchange. Cryptographic erasure destroys the key needed to read encrypted information [2,3]. The encrypted bytes may remain, while a readable cached copy requires separate removal. A deletion receipt records what the system claims to have completed. Consequently, neither a hidden name on screen nor a successful receipt alone establishes the state of every copy.

For example, if an erased diagnosis appears as “inactive” in an export, a recipient could interpret it as a change in the patient's condition. HL7 Fast Healthcare Interoperability Resources (FHIR) defines structured resources for exchanging such information [8,9]. An export must therefore convey both an acceptable structure and a meaning justified by the record's state. This example motivates our evaluation; we did not study clinician behaviour or patient outcomes.

GDPR Article 17 defines grounds and exceptions for erasure [1]. We evaluate technical consistency after a request, rather than deciding when a medical record should legally be erased. CryptoShred Health is an envelope-encrypted EHR prototype [4] whose performance is reported separately [5]. We compare policy metadata, storage state, application responses, receipts and exports during normal operation and two selected failures. The contribution is a reproducible method linking each erasure claim to a separate observation, not a new cryptographic primitive or an estimate of deployment reliability.

## Methods

### Prototype and execution environment

The Java 21/Spring Boot 3.3.4 prototype stores encrypted records and metadata in PostgreSQL, decrypted responses in Redis and events through Kafka. Vault Transit manages key-encryption keys (KEKs) wrapping data-encryption keys (DEKs). FHIR exports group resources into Bundles. Two MedicationStatement R4 fields had previously been corrected using a strict parser; the erasure workflow was unchanged.

Commit 436d4d662315e82de62df07776c449f02d26bae3 ran in three isolated GitHub Actions jobs with fresh databases and services. Each built the application JAR and ran scenarios as the seeded DOCTOR role against PostgreSQL 15, Redis 7, Kafka 3.7.0 and one development-mode Vault 1.13.3 instance. Only synthetic records were created. Versioned evidence contains observations, exports and diagnostics; complete logs and receipts were captured as run artifacts [6].

### Scenarios and observations

Source-guided selection covered six concerns in four sequences (Table 1), with four patients and one visit per deployment. Direct database, Vault and Redis observations were compared with API responses and receipt claims. Checks covered the named cache entry, tested name, shredded flags and KEK reference, not every field or copy. Outcomes were Boolean observations and HTTP results; no reliability estimates were calculated.

Table 1. Scenario protocol and independent observations.

| ID | Operation or injected condition | Principal observation |
|---|---|---|
| S1 | Erase a recently created patient without an override reason | Retention classification and acceptance |
| S2 | Complete patient-level erasure | Tested name redacted and Redis key absent |
| S3 | Erase one clinical visit | Visit flagged shredded and patient name retained |
| S4 | Deny Redis DEL while allowing GET | Residual plaintext, API response and receipt claim |
| S5 | Keep a snapshot made before visit erasure | Vault unwrap before/after and snapshot fingerprint |
| S6 | Reject SQL update after external key destruction | Request error, SQL row, Vault key and subsequent GET |

S4 denied Redis DEL after cache warming. S6 used a PostgreSQL trigger to reject one patient update; SQL inspection preceded the subsequent GET. Both fault controls were removed in finally blocks.

S5 checked Vault unwrap using the snapshot's wrapped DEK and KEK reference, KEK absence and unchanged snapshot SHA-256. This tests that key path, not certified immutable media or absence of other key copies.

### FHIR assessment and evidence interpretation

Each deployment produced three live Bundles: after patient erasure, before visit erasure and after visit erasure. We assessed unmodified JSON with HAPI FHIR 8.8.2 and base R4 definitions [7]. Terminology checks were disabled, UK Core packages were not loaded, and unknown profiles were not configured as errors. All messages and OperationOutcome resources were retained. This used an external validator implementation, not independent investigators. Successful scenario execution and valid FHIR were separate outcomes.

Clinical-status changes were inspected against R4 definitions [8]: accepting a code does not establish its clinical justification. Mocked component tests supported regression checks and were not counted as live deployments.

## Results

### Workflow outcomes

All four sequences completed with matching observations across three deployments. In S1, the patient response reported PROTECTED, yet the request succeeded without an explicit override. The receipt retained PROTECTED and supplied STANDARD_REQUEST as its reason. This tested endpoint records retention classification without requiring a separately supplied override. PROTECTED is a prototype label; neither it nor this experiment determines the legally appropriate retention decision.

In S2, the patient's firstName became [SHREDDED], its response flag was true and the Redis key was absent. In S3, the visit endpoint reported shredded=true while the patient's original firstName remained available. In S5, Vault unwrap returned HTTP 200 before erasure; afterwards KEK lookup returned 404 and the same unwrap request returned 400. The snapshot fingerprint remained unchanged. These are observations of the tested fields and key path, not exhaustive absence-of-plaintext checks.

S4 exposed disagreement between storage and evidence. Redis still contained the synthetic name after DEL was denied. The patient API nevertheless returned a redacted representation, consistent with its database-state guard. The emitted receipt reported ALL_PATIENT_CACHES_EVICTED. Consequently, suppression through the application read path did not demonstrate removal of plaintext from the cache, and the receipt overstated the directly observed effect.

In S6, the erasure request returned HTTP 500. The subsequent SQL inspection found shredded=false and ciphertext present, while Vault returned 404 for the KEK. A later GET reported shredded=true without the original name. Thus, API representation differed from the SQL state observed immediately after failure. We did not re-query SQL after that GET or test whether a later operation repaired the inconsistency. The failed metadata update did not reverse external key destruction.

### Interoperability outputs

The exports contained one resource after patient erasure, three before visit erasure and five afterwards. Redacted placeholders introduced previously absent AllergyIntolerance and MedicationStatement resources; resource count cannot indicate retained clinical information.

All nine live Bundles produced validation errors. For each export position, resource counts and diagnostic counts were identical across the three deployments (Table 2). Errors included timestamps without timezone information, an invalid OID identifier system, relative entry fullUrl values and violation of bdl-1 through use of total in a collection Bundle [9]. Warnings included absent narratives and unavailable UK Core profile definitions. Error counts describe these fixtures and validator settings, not a general interoperability score.

Table 2. Base R4 validator diagnostics per Bundle in each of three deployments.

| Export position | Resources | Errors | Warnings | Info |
|---|---|---|---|---|
| After patient erasure | 1 | 4 | 2 | 0 |
| Before visit erasure | 3 | 7 | 6 | 3 |
| After visit erasure | 5 | 9 | 10 | 7 |

Inspection also confirmed that the Condition clinicalStatus changed from active to inactive after erasure. In R4, inactive expresses a judgement about symptoms or evidence of the condition [8]; loss of decryptability does not provide that evidence. The REDACTED marker was placed in meta.tag. A general tag does not by itself establish a security-label enforcement contract, which FHIR represents separately [10]. We did not test downstream consumers or measure clinical consequences.

## Discussion

The protocol distinguishes five assertions: permission to proceed, loss of a decryption path, persisted workflow status, suppression of disclosure and faithful clinical representation. They require different observations. S4 demonstrates that suppression and cache removal can disagree; S6 demonstrates that a redacted response does not establish a committed deletion flag. These comparisons turn individual defects into explicit evaluation requirements for an erasure-capable EHR.

The database guard suppressed disclosure through the patient endpoint while plaintext remained retrievable from Redis. Receipts should distinguish requested from confirmed eviction and expose unresolved effects to authorised operators. Receipt integrity cannot establish the truth of an unobserved storage claim or extend its scope to exported copies.

For an authorised operator, a partial-completion state should explain which action failed and whether escalation is needed. The metadata failure illustrates this need when key destruction succeeds but persistence fails. This concerns interruption of a current request, not restoration of historical keys. Neither a distributed transaction protocol nor the prototype's backup-recovery and tombstone mechanisms are evaluated here.

Erasure should not manufacture a clinical status or previously absent resource. FHIR's masked absence reason [11] is an option where permitted, not a universal redaction recipe. Element constraints, disclosure policy and consumer expectations still apply. Even an erasure marker may be inappropriate where revealing a record's existence is prohibited.

This system-facing analysis complements SECURE-CDS's user-facing cyber-resilience perspective [12]: source verification and escalation require faithful information about availability. No training intervention, AI model or clinical decision was evaluated. Performance [5] and recovery-safe erasure remain separate from the present contribution.

The study is limited to one author-associated prototype, one role, small fixtures and two deterministic faults. Three fresh deployments repeat the same experiment; they do not constitute independent replication or estimate failure rates. Field-level checks do not establish complete redaction. Vault development mode and a single broker limit production generalisation. Kafka delivery was not independently asserted. Validator settings exclude terminology and UK Core conformance, while structural acceptance cannot establish clinical intent. We did not assess anonymity, clinical harm, WORM certification or legal compliance.

## Conclusions

Comparing claims with observations exposed retention metadata without an explicit override gate, residual cache plaintext despite an eviction receipt, and divergent SQL and API states after external key destruction. External FHIR validation and semantic inspection exposed additional export limitations. The reusable outcome is a bounded evaluation protocol: policy decisions, storage effects, disclosure and clinical representation need separate evidence. Its clinical usefulness and applicability across EHR implementations remain to be evaluated.

## References

[1] European Parliament, Council of the European Union. Regulation (EU) 2016/679. Off J Eur Union. 2016;L119:1-88. Article 17.

[2] Chandramouli R, Hibbard E. Guidelines for Media Sanitization. NIST SP 800-88 Rev. 2. 2025. doi:10.6028/NIST.SP.800-88r2.

[3] Geambasu R, Kohno T, Levy AA, Levy HM. Vanish: Increasing Data Privacy with Self-Destructing Data. In: 18th USENIX Security Symposium. USENIX Association; 2009.

[4] Hevesi R. Beyond Physical Deletion: Enforcing Verifiable Cryptographic Erasure Across Distributed Storage Layers in Zero-Plaintext Electronic Health Record Architectures [master's dissertation]. Politehnica University Timisoara; 2026.

[5] Hevesi R, Iovanovici A. Performance Evaluation of an Envelope-Encrypted Electronic Health Record Architecture with Managed Keys and Blind Indexing. RoEduNet 2026. Accepted manuscript; 2026.

[6] Hevesi R, Iovanovici A. CryptoShred Health MIE 2027 evaluation code and evidence. 2026. https://github.com/iovanalex/cryptoshred-health/tree/paper/mie2027-evaluation. Accessed 15 October 2026.

[7] HAPI FHIR. Instance Validator. https://hapifhir.io/hapi-fhir/docs/validation/instance_validator.html. Accessed 15 October 2026.

[8] HL7 International. FHIR R4 Condition Clinical Status Codes. 2019. https://hl7.org/fhir/R4/valueset-condition-clinical.html.

[9] HL7 International. FHIR R4 Bundle. 2019. https://hl7.org/fhir/R4/bundle.html.

[10] HL7 International. FHIR R4 Base Resource Definitions. 2019. https://hl7.org/fhir/R4/resource.html.

[11] HL7 International. FHIR R4 DataAbsentReason. 2019. https://hl7.org/fhir/R4/codesystem-data-absent-reason.html.

[12] Iovanovici A, Crisan-Vida M. Cyber-Resilient AI Literacy for Clinical Decision Support: A Competency Framework. EFMI STC 2026. Accepted manuscript; 2026.
