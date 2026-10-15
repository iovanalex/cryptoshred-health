# Erasure Workflows and Residual Record State in a Distributed EHR

Robert HEVESI and Alexandru IOVANOVICI

Politehnica University Timisoara, Faculty of Automation and Computers, Timisoara, Romania

Corresponding author: Alexandru Iovanovici, alexandru.iovanovici@upt.ro

## Abstract

Cryptographic erasure removes a decryption capability, but an electronic health record (EHR) also exposes database state, plaintext caches, deletion receipts and interoperable exports. We evaluated their consistency in CryptoShred Health using authenticated HTTP requests against an application JAR and real PostgreSQL, Redis, Kafka and Vault services. Six concerns were exercised in four scenario groups across three fresh deployments. An external validator assessed unmodified exports against base HL7 FHIR R4 structure and invariants. Normal patient erasure redacted the tested name; visit erasure left the patient's name available. A retained encrypted snapshot remained byte-identical while its Vault unwrapping path became unavailable. However, a request classified PROTECTED was accepted without an explicit override; denied cache eviction left plaintext despite a receipt asserting complete eviction; and failed SQL persistence left an unmarked record after external key destruction. All nine live Bundles produced R4 validation errors. The contribution is a reproducible evaluation that compares policy metadata, storage observations, API disclosure and receipt claims, and separates structural validation from clinical meaning. Findings concern one synthetic-data prototype; they do not establish comprehensive erasure, clinical effectiveness or legal compliance.

Keywords: electronic health records; cryptographic erasure; data governance; fault injection; HL7 FHIR; semantic interoperability

## Introduction

An EHR may withhold a diagnosis after erasure, access restriction or service failure. None establishes clinical resolution. A successful deletion response likewise does not establish removal of cached plaintext or commitment of every storage operation. Erasure has observable outcomes beyond key destruction.

GDPR Article 17 defines grounds and exceptions for erasure [1]. We examine whether a prototype distinguishes retention classification from execution and whether its claims match observable effects. NIST guidance treats sanitisation as rendering access infeasible within a defined effort model [2]. Key-based approaches [3] motivate examining decryptability, but cannot alone establish application-wide removal of plaintext or meaningful clinical representation.

CryptoShred Health is an envelope-encrypted EHR prototype [4] whose transaction performance is evaluated separately [5]. Our contribution is a reproducible evaluation protocol linking each erasure claim to an observable state, exercised through two deterministic faults and live FHIR assessment. We ask which outcomes agree across normal and partial-failure paths, and which apparent assurances exceed the available evidence. The transferable contribution is this claim-to-observation method and the requirements it exposes, rather than a new deletion primitive or an estimate of deployment reliability.

## Methods

### Prototype and execution environment

The Java 21 and Spring Boot 3.3.4 prototype uses PostgreSQL for encrypted payloads and metadata, Vault Transit for key-encryption keys (KEKs) wrapping data-encryption keys (DEKs), Redis for decrypted responses and Kafka for events. It exports encrypted visit snapshots and FHIR Bundles. Two MedicationStatement R4 fields had previously been corrected using a strict parser; the erasure workflow was unchanged.

Commit 436d4d662315e82de62df07776c449f02d26bae3 ran in three isolated GitHub Actions jobs with fresh databases and services. Each built the application JAR and ran scenarios as the seeded DOCTOR role against PostgreSQL 15, Redis 7, Kafka 3.7.0 and one development-mode Vault 1.13.3 instance. Only synthetic records were created. Versioned evidence contains observations, exports and diagnostics; complete logs and receipts were captured as run artifacts [6].

### Scenarios and observations

Source inspection guided selection of normal paths and suspected inconsistencies. Six concerns formed four sequences: S1/S2, S3/S5, S4 and S6 (Table 1). Each deployment created four patients and one visit. Database, Vault and Redis states were inspected directly, separately from API responses. A receipt claim was supported only when its corresponding observation agreed; endpoint success alone was insufficient. Checks covered the named cache entry, tested name, shredded flags and KEK reference, not every field or copy. Outcomes were Boolean observations and HTTP results, without timing or inferential statistics.

Table 1. Scenario protocol and independent observations.

| ID | Operation or injected condition | Principal observation |
|---|---|---|
| S1 | Erase a recently created patient without an override reason | Retention classification and acceptance |
| S2 | Complete patient-level erasure | Tested name redacted and Redis key absent |
| S3 | Erase one clinical visit | Visit flagged shredded and patient name retained |
| S4 | Deny Redis DEL while allowing GET | Residual plaintext, API response and receipt claim |
| S5 | Keep a snapshot made before visit erasure | Vault unwrap before/after and snapshot fingerprint |
| S6 | Reject SQL update after external key destruction | Request error, SQL row, Vault key and subsequent GET |

For S4, Redis temporarily denied DEL after cache warming; its residual content was compared with the API response and receipt. For S6, a PostgreSQL trigger rejected updates to one patient. After the failed request, we inspected its shredded flag, ciphertext, Vault key and subsequent GET. Both fault controls were removed in finally blocks.

For S5, we used the snapshot's wrapped DEK and KEK reference to check Vault unwrap before and after erasure, KEK absence and snapshot byte identity through SHA-256. This tests the retained snapshot's unwrapping path, not certified WORM media or absence of alternative key copies.

### FHIR assessment and evidence interpretation

Each deployment produced three live Bundles: after patient erasure, before visit erasure and after visit erasure. We assessed unmodified JSON with HAPI FHIR 8.8.2 and base R4 definitions [7]. Terminology checks were disabled, UK Core packages were not loaded, and unknown profiles were not configured as errors. All messages and OperationOutcome resources were retained. This used an external validator implementation, not independent investigators. Successful scenario execution and valid FHIR were separate outcomes.

We also inspected the emitted clinical-status transformation against the R4 definition [8]. A parser can recognise an element, and an instance validator can accept its code, without establishing that an erasure event justifies the clinical assertion. The existing component suite provided supporting regression evidence; its mocked tests were not counted as live scenarios or independent deployments.

## Results

### Workflow outcomes

All four sequences completed with matching observations across three deployments. In S1, the patient response reported PROTECTED, yet the request succeeded without an explicit override. The receipt retained PROTECTED and supplied STANDARD_REQUEST as its reason. This tested endpoint records retention classification without requiring a separately supplied override. PROTECTED is a prototype label; neither it nor this experiment determines the legally appropriate retention decision.

In S2, the patient's firstName became [SHREDDED], its response flag was true and the Redis key was absent. In S3, the visit endpoint reported shredded=true while the patient's original firstName remained available. In S5, Vault unwrap returned HTTP 200 before erasure; afterwards KEK lookup returned 404 and the same unwrap request returned 400. The snapshot fingerprint remained unchanged. These are observations of the tested fields and key path, not exhaustive absence-of-plaintext checks.

S4 exposed disagreement between storage and evidence. Redis still contained the synthetic name after DEL was denied. The patient API nevertheless returned a redacted representation, consistent with its database-state guard. The emitted receipt reported ALL_PATIENT_CACHES_EVICTED. Consequently, suppression through the application read path did not demonstrate removal of plaintext from the cache, and the receipt overstated the directly observed effect.

In S6, the erasure request returned HTTP 500. The subsequent SQL inspection found shredded=false and ciphertext present, while Vault returned 404 for the KEK. A later GET reported shredded=true without the original name. Thus, API representation differed from the SQL state observed immediately after failure. We did not re-query SQL after that GET or test whether a later operation repaired the inconsistency. The failed metadata update did not reverse external key destruction.

### Interoperability outputs

The exports contained one resource after patient erasure, three before visit erasure and five afterwards. Redacted placeholders triggered AllergyIntolerance and MedicationStatement resources absent from the pre-erasure Bundle. Resource counts therefore cannot represent the amount of retained clinical information.

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

The metadata failure motivates a partial-completion state and escalation when key destruction succeeds but persistence fails. This concerns interruption of a current request, not restoration of historical keys. Neither a distributed transaction protocol nor the prototype's backup-recovery and tombstone mechanisms are evaluated here.

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
