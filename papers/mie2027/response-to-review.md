# Response to the supplied scientific review

This revision uses the same evaluated application commit and existing three live
executions. `analyse_retained_evidence.py` adds reproducible, post-hoc analysis of
retained outputs. No new broker-consumption experiment or robustness trial is
claimed. Authors remain Adina Nitulescu, Robert Hevesi, Mihaela Crisan-Vida and
Alexandru Iovanovici, in that order.

## Major issues

1. **Protocol asserted rather than presented.** Table 1 now provides the five
   assertions, the required observations, an expected outcome with its basis,
   and scenario mapping. Methods explicitly identifies this as a retrospective
   formalisation of the source-guided evaluation. It is not presented as a
   pre-registered protocol or an independently validated standard.
2. **Expected outcomes and S1.** Criteria distinguish service-contract effects
   (D), FHIR semantics (F) and proposed operational requirements (P). Inspection
   of `forgetPatient` and `forgetVisit` confirms that PROTECTED permits a request
   with a default STANDARD_REQUEST reason. The available design describes a
   rolling horizon but does not establish an override-blocking contract. We
   therefore do not manufacture a failed specification test or derive a
   blocking rule directly from GDPR. S1 is a conditional policy criterion and
   an unresolved gate specification. S2/S3/S5 have normal-effect criteria;
   S4/S6 distinguish receipt truth and durable completion from API success.
3. **Baseline versus induced FHIR diagnostics.** The abstract no longer headlines
   nine invalid Bundles. There are three export positions, repeated three times;
   the principal contrast is the paired visit export. Table 2 reports 3→5
   resources, 7→9 errors and 6→10 warnings. The additional errors are two new
   relative-fullUrl occurrences, not new error classes. Added warnings are two
   narrative warnings and two unresolved-profile warnings. Existing timezone,
   OID and collection-total defects are baseline findings. Semantic differences
   are analysed separately from validator diagnostic counts.
4. **Clinical finding undersold.** The abstract and first Results subsection now
   lead with newly generated placeholder AllergyIntolerance and
   MedicationStatement resources and the active→inactive Condition transition.
   Retained JSON additionally confirms verificationStatus=confirmed on the new
   allergy. These are unsupported clinical representations, not evidence that
   a real allergy or medication was present. We do not claim measured harm.
5. **Excessive caveats.** General scope limits are consolidated in Limitations.
   Qualifications that define an observation's meaning remain beside that
   observation: S1's unspecified rule, source-only Kafka findings and diagnostic
   deltas cannot be deferred without making those results misleading.
6. **Residual stores.** A source audit now follows creation/erasure event
   builders, event DTO and publisher. It finds encrypted creation payloads but
   readable patient/event/key identifiers and timestamps; erasure events retain
   metadata. This is not broker consumption or evidence of delivery. WAL and
   historical backups are explicitly excluded from this current-workflow study;
   the snapshot result covers only the tested decryption path. These limits
   are retained rather than claiming system-wide erasure.
7. **Scenario selection and realism.** Methods now names the source trace,
   normal paths and boundaries selected for deterministic failure. Redis DEL
   denial models command-permission drift, not a network partition. The SQL
   trigger models persistence rejection such as a constraint failure, not a
   timing/timeout model. Selection was implementation-informed and purposive.

## Methodological clarifications

- **S6 ordering:** the erasure workflow itself destroys the KEK before SQL
  persistence completes. The external deletion survives rollback. Discussion
  proposes durable intent, idempotent execution, persisted completion and
  retry/escalation; an outbox/saga-style design is a candidate, not a tested fix.
  The manuscript does not infer the SQL state after the subsequent GET.
- **Receipts:** Methods now describes fields, audit/Merkle data, RSA and ML-DSA
  signatures, cache/event ordering and transaction timing. Source inspection of
  `buildCanonicalSignPayload` shows that signatures cover identifier,
  timestamp, audit hash and Merkle root rather than all receipt JSON fields.
  In particular layerStatus is not directly included in the canonical fields.
  This is descriptive scope, not a new proof-security evaluation reserved for
  the journal work.
- **Demographic checks:** retained S2 Patient FHIR outputs from all repetitions
  now explicitly verify given/family=[SHREDDED], absent birthDate and retained
  synthetic identifier. These are additional export checks; no uncaptured
  patient API lastName/dateOfBirth check is claimed.
- **Repetitions:** deterministic repetitions are labelled repeatability, not
  robustness, failure-rate estimation or independent replication.

## Minor issues

- Title now names fault injection and FHIR export semantics, and drops
  “distributed” as an implicit generalisation. Prototype scope is explicit in
  the abstract and Methods.
- Abstract opens with the clinical interpretation problem.
- Removed the strict-parser correction, mocked-test explanation, external
  investigator caveat and SECURE-CDS linkage. Removed the dissertation and
  accepted-manuscript references from the manuscript; the repository remains
  as the implementation/evidence reference.
- Added verified Reardon/Basin/Capkun and Politou/Alepis/Patsakis references,
  official OWASP logging guidance and HL7 security-label documentation.
- Discussion recommends meta.security using REDACTED from v3 ObservationValue
  where policy permits, and masked data absence where element constraints
  allow. It mentions con-3 as a best-practice recommendation and con-5 as a
  prohibition under entered-in-error. It does not prescribe false
  entered-in-error status as an erasure workaround.
- NIST SP 800-88 Rev. 2 verified against the final CSRC record: Ramaswamy
  Chandramouli and Eric Hibbard, September 2025 (final 26 September).
- **Blinding remains unspecified publicly:** checked the MIE 2027 Instructions
  for Authors, CFP and public submission landing page on 15 October 2026. They
  do not state an anonymisation rule. This is not confirmation that the
  signed-in submission form imposes none. The named-author master is preserved.

## Sources checked

- https://mie2027.efmi.org/call-for-papers/instruction-for-authors
- https://mie2027.efmi.org/call-for-papers
- https://access.online-registry.net/mie2027/
- https://csrc.nist.gov/pubs/sp/800/88/r2/final
- https://syssec.ethz.ch/publications/2013-05-19-sok-secure-data-deletion-20-500-11850-70466/
- https://academic.oup.com/cybersecurity/article/4/1/tyy001/4954056
- https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- https://hl7.org/fhir/R4/condition-definitions.html
- https://hl7.org/fhir/R4/security-labels.html
- https://hl7.org/fhir/R4/v3/ObservationValue/cs.html
- https://hl7.org/fhir/R4/codesystem-data-absent-reason.html

## Follow-up review addressed 18 October 2026

- D criteria are now explicitly attributed to the pre-existing service contract;
  only P criteria are proposed here. S4 contradicts a prior eviction commitment.
  Post-hoc S2 export checks are explicitly identified as additional observations,
  not pre-specified tests.
- Removed “external” from the S6 key-destruction result.
- Results now connects S4 to caught/logged eviction exceptions and an eviction
  claim unconditioned on the DEL result. Receipt construction before SQL commit
  and after asynchronous event submission is stated there.
- Results separately reports the canonical signature fields and exclusion of
  layerStatus. This source-based finding does not imply a signature-forgery
  experiment or proof-strength evaluation.
- Kafka metadata findings have a separate paragraph.
- Abstract explicitly identifies one prototype using synthetic data. CI jobs are
  named; the opening clinical motivation is written in connected prose.
- Table 1 has an explanatory note for D/F/P and distinguishes S2 Patient export
  from S3 paired visit exports.
- Added two verified clinical-informatics papers: Lee et al., Applied Clinical
  Informatics 2025, doi:10.1055/a-2466-4371 (FHIR consent-based segmentation);
  Malin and Airoldi, Studies in Health Technology and Informatics 2007;129(Pt 1):
  320-324 (sensitive information exposed when linking medical-record access
  logs). The latter supports confidentiality risks in audit linkage, not an
  assertion that every application log contains plaintext clinical payloads.
  The original OWASP guidance is retained alongside the peer-reviewed evidence.
- References were renumbered in first-citation order, now 13 entries.
- Rechecked public MIE author instructions and submission landing page on
  18 October: neither states an anonymisation rule. The authenticated form was
  not inspected; absence of a public rule is not confirmation of no blinding.
- Wording was shortened around repeated table explanations to maintain five
  pages with bibliography margin, without shrinking fonts or margins.

Additional sources verified:
- https://asu.elsevierpure.com/en/publications/fhir-granular-sensitive-data-segmentation/
- https://pubmed.ncbi.nlm.nih.gov/17911731/
