# Erasure Workflows and Residual Record State in a Distributed EHR

Robert HEVESI and Alexandru IOVANOVICI

Politehnica University Timisoara, Faculty of Automation and Computers, Timisoara, Romania

Corresponding author: Alexandru Iovanovici, alexandru.iovanovici@upt.ro

## Abstract

Cryptographic erasure removes a decryption capability, but an electronic health record (EHR) also exposes database state, plaintext caches, deletion receipts and interoperable exports. We evaluated their consistency in CryptoShred Health using authenticated HTTP requests against a production application build and real PostgreSQL, Redis, Kafka and Vault services. Six concerns were exercised in four scenario groups, including controlled Redis and SQL failures, across three fresh deployments. Unmodified live exports were independently assessed against base HL7 FHIR R4 structure and invariants. Normal patient erasure suppressed demographic disclosure, and visit erasure preserved patient demographics. A pre-erasure encrypted snapshot remained byte-identical while key unwrapping became unavailable. However, retention-protected requests were accepted; denied cache eviction left plaintext in Redis despite a receipt asserting complete eviction; and SQL rollback left an unmarked record after its key had been destroyed. All nine live Bundles produced R4 validation errors. These findings distinguish policy decisions, storage effects, API disclosure and evidence claims. The contribution is a reproducible scenario-based evaluation of one synthetic-data prototype, without claims of clinical effectiveness, comprehensive deletion or legal compliance.

Keywords: electronic health records; cryptographic erasure; data governance; fault injection; HL7 FHIR; semantic interoperability

## Introduction

An EHR can stop returning a diagnosis because a record has been erased, access has been restricted, or a dependency has failed. None establishes that the condition has resolved. A successful deletion response likewise does not establish removal of cached plaintext or commitment of every storage operation. Erasure has an observable outcome beyond key destruction.

GDPR Article 17 defines grounds and exceptions for erasure [1]. We examine whether a prototype distinguishes retention classification from execution and whether its claims match observable effects. NIST guidance treats sanitisation as rendering access infeasible within a defined effort model [2]. Key-based approaches [3] motivate examining decryptability, but cannot alone establish application-wide removal of plaintext or meaningful clinical representation.

CryptoShred Health is an envelope-encrypted EHR prototype [4] whose transaction performance is evaluated separately [5]. We contribute a scenario protocol, deterministic fault injection at two workflow boundaries and assessment of live FHIR outputs. We ask whether retention metadata, key availability, persisted state, API responses and receipts remain consistent under normal and partial-failure conditions, while distinguishing standards validation from clinical meaning.

## Methods

### Prototype and execution environment

The Java 21 and Spring Boot 3.3.4 prototype uses PostgreSQL for encrypted payloads and metadata, Vault Transit for key-encryption keys (KEKs) wrapping data-encryption keys (DEKs), Redis for decrypted responses and Kafka for events. It exports encrypted visit snapshots and FHIR Bundles. Two MedicationStatement R4 fields had previously been corrected using a strict parser; the erasure workflow was unchanged.

Commit 436d4d662315e82de62df07776c449f02d26bae3 ran in three isolated GitHub Actions jobs with fresh databases and services. Each built the production JAR and ran authenticated HTTP scenarios against PostgreSQL 15, Redis 7, Kafka 3.7.0 and one development-mode Vault 1.13.3 instance. Only synthetic records were created. Logs, receipts, exports, image identifiers and checksums were retained [6].

### Scenarios and observations

Six concerns formed four sequences: S1/S2, S3/S5, S4 and S6 (Table 1). Each deployment created four patients and one visit. Database, Vault and Redis states were inspected directly, independently of application responses. Outcomes were Boolean observations and HTTP results, without timing or inferential statistics.

Table 1. Scenario protocol and independent observations.

| ID | Operation or injected condition | Principal observation |
|---|---|---|
| S1 | Erase a recently created patient without an override reason | Retention classification and acceptance |
| S2 | Complete patient-level erasure | Redacted API response and Redis key absence |
| S3 | Erase one clinical visit | Shredded visit with retained patient demographics |
| S4 | Deny Redis DEL while allowing GET | Residual plaintext, API response and receipt claim |
| S5 | Keep a snapshot made before visit erasure | Vault unwrap before/after and snapshot fingerprint |
| S6 | Reject SQL update after external key destruction | Request error, SQL row, Vault key and subsequent GET |

For S4, Redis temporarily denied DEL after cache warming; its residual content was compared with the API response and receipt. For S6, a PostgreSQL trigger rejected updates to one patient. After the failed request, we inspected its shredded flag, ciphertext, Vault key and subsequent GET. Both fault controls were removed in finally blocks.

For S5, we used the snapshot's wrapped DEK and KEK reference to check Vault unwrap before and after erasure, KEK absence and snapshot byte identity through SHA-256. This tests the retained snapshot's unwrapping path, not certified WORM media or absence of alternative key copies.

### FHIR assessment and evidence interpretation

Each deployment produced three live Bundles: after patient erasure, before visit erasure and after visit erasure. HAPI FHIR 8.8.2 independently evaluated their unmodified JSON using the base R4 definitions and instance validator [7]. Terminology checks were disabled, UK Core packages were not loaded, and unknown profiles were not configured as errors. We retained all diagnostic messages and OperationOutcome resources. Validator execution was checked separately from validator success: invalid exports are study findings, not failed execution of the experiment.

We also inspected the emitted clinical-status transformation against the R4 definition [8]. A parser can recognise an element, and an instance validator can accept its code, without establishing that an erasure event justifies the clinical assertion. The existing component suite provided supporting regression evidence; its mocked tests were not counted as live scenarios or independent deployments.

## Results

### Workflow outcomes

All four scenario sequences completed in each of the three deployments. S1 returned PROTECTED before erasure, yet the request was accepted without an explicit override, and its receipt retained that classification. Thus, this endpoint records retention status but does not enforce it as a deletion gate. This observation concerns the implemented policy path, not whether erasure would be legally permitted in a particular clinical setting.

Under normal conditions, S2 returned a shredded patient representation and removed the corresponding Redis key. S3 shredded the visit while the patient endpoint retained the original synthetic name. In S5, Vault unwrap returned HTTP 200 before erasure; afterwards KEK lookup returned 404 and the same unwrap request returned 400. The snapshot fingerprint remained unchanged. These observations were consistent across deployments.

S4 exposed disagreement between storage and evidence. Redis still contained the synthetic name after DEL was denied. The patient API nevertheless returned a redacted representation, consistent with its database-state guard. The emitted receipt reported ALL_PATIENT_CACHES_EVICTED. Consequently, suppression through the application read path did not demonstrate removal of plaintext from the cache, and the receipt overstated the directly observed effect.

In S6, the erasure request returned HTTP 500. The database transaction rolled back, leaving shredded=false and ciphertext present, but Vault returned 404 for the KEK. A subsequent GET returned a shredded representation without the original name. The API therefore presented an inferred availability state that differed from the persisted flag. SQL rollback did not reverse the external key destruction. We did not test repair, retry safety or every possible failure position.

### Interoperability outputs

The live exports contained one resource after patient erasure, three before visit erasure and five after visit erasure. The latter increase arose because redacted placeholder strings caused AllergyIntolerance and MedicationStatement resources to be emitted, although these resources were absent before erasure. This illustrates why resource counts cannot serve as a proxy for retained clinical information.

All nine live Bundles produced validation errors. For each export position, resource counts and diagnostic counts were identical across the three deployments (Table 2). Errors included timestamps without timezone information, an invalid OID identifier system, relative entry fullUrl values and violation of bdl-1 through use of total in a collection Bundle [9]. Warnings included absent narratives and unavailable UK Core profile definitions. Error counts describe these fixtures and validator settings, not a general interoperability score.

Table 2. Base R4 validator diagnostics per Bundle in each of three deployments.

| Export position | Resources | Errors | Warnings | Info |
|---|---|---|---|---|
| After patient erasure | 1 | 4 | 2 | 0 |
| Before visit erasure | 3 | 7 | 6 | 3 |
| After visit erasure | 5 | 9 | 10 | 7 |

Inspection also confirmed that the Condition clinicalStatus changed from active to inactive after erasure. In R4, inactive expresses a judgement about symptoms or evidence of the condition [8]; loss of decryptability does not provide that evidence. The REDACTED marker was placed in meta.tag. A general tag does not by itself establish a security-label enforcement contract, which FHIR represents separately [10]. We did not test downstream consumers or measure clinical consequences.

## Discussion

An erasure outcome spans different kinds of state: permission to proceed, decryptability, persisted coordination metadata, residual plaintext and clinical representation. Their agreement cannot be inferred from a successful response or signed receipt.

The database guard suppressed disclosure through the patient endpoint while plaintext remained retrievable from Redis. Receipts should distinguish requested from confirmed eviction and expose unresolved effects to authorised operators. Receipt integrity cannot establish the truth of an unobserved storage claim or extend its scope to exported copies.

Local transactional guarantees could not reverse external key destruction. The observed divergence motivates explicit partial-completion states and reconciliation or escalation when metadata persistence fails. We do not implement a distributed transaction protocol or evaluate historical key-store recovery.

Clinical meaning creates a further obligation. A privacy-driven transition should not manufacture a status change or a previously absent clinical resource. FHIR provides mechanisms for representing unavailable data, including a masked absence reason in appropriate contexts [11], but neither such a code nor a local tag is a universal redaction recipe. Element constraints, disclosure policy and consumer expectations must be considered together. Where revealing even the existence of a record is prohibited, communicating an erasure marker may itself be inappropriate.

This system-facing analysis complements SECURE-CDS's user-facing cyber-resilience perspective [12]: source verification and escalation require faithful information about availability. No training intervention, AI model or clinical decision was evaluated. Performance [5] and recovery-safe erasure remain separate from the present contribution.

The study is limited to one author-associated prototype, small synthetic fixtures and two deterministic injected faults. Three fresh deployments establish repeatability of these observations, not population-level reliability. Vault development mode, locally permissive test credentials and a single broker limit production generalisation. Kafka was a real dependency, but delivery and persistence guarantees were not independently asserted. FHIR validation excluded terminology and UK Core profiles, and syntactic or structural acceptance cannot validate clinical intent. We did not establish anonymity of retained identifiers, universal erasure, WORM certification or legal compliance.

## Conclusions

A scenario-based evaluation of a distributed EHR distinguished successful redaction and key loss from unenforced retention metadata, residual cache plaintext, overstated receipts and divergent SQL state. Independent FHIR assessment further bounded the interoperability claim. Erasure-capable EHRs need explicit policy decisions, observed storage outcomes and faithful residual representations. These obligations can be evaluated using reproducible functional scenarios without republishing performance or historical recovery experiments.

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
