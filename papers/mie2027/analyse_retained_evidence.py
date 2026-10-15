"""Reanalyse retained live outputs; does not execute or modify the EHR.

Run from any directory. Diagnostic deltas are paired visit comparisons, not
independent samples. Additional demographic checks concern FHIR, not uncaptured
patient API fields. Source review is explicitly separate from live observations.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

def load(path):
    return json.loads(path.read_text())

def signature(issue):
    # Repeated reference-resolution information is not counted as new errors.
    return (issue['severity'], issue.get('diagnostics', ''))

out = {'analysis_type': 'post-hoc retained-output analysis', 'repetitions': []}
for n in (1, 2, 3):
    d = ROOT / 'evidence' / f'repetition-{n}'
    before = load(d / 'visit-fhir-before.json')['entry']
    after = load(d / 'visit-fhir-after.json')['entry']
    p = load(d / 'patient-fhir-after.json')['entry'][0]['resource']
    assert p['resourceType'] == 'Patient'
    demographic = {
        'given_redacted': p['name'][0]['given'] == ['[SHREDDED]'],
        'family_redacted': p['name'][0]['family'] == '[SHREDDED]',
        'birthDate_absent': 'birthDate' not in p,
        'identifier_retained': p['identifier'][0]['value'] == 'MIE-PATIENT',
    }
    assert all(demographic.values())
    issues = [load(d / 'fhir-validation' / f'visit-fhir-{pos}.json.outcome.json')['issue']
              for pos in ('before', 'after')]
    counts = [Counter(i['severity'] for i in x) for x in issues]
    delta = Counter(signature(i) for i in issues[1]) - Counter(signature(i) for i in issues[0])
    delta = [{'severity': k[0], 'diagnostic': k[1], 'count': v}
             for k, v in delta.items() if k[0] in ('error', 'warning')]
    condition = lambda entries: next(e['resource'] for e in entries
                                     if e['resource']['resourceType'] == 'Condition')
    added = [e['resource'] for e in after if e['resource']['resourceType']
             not in {x['resource']['resourceType'] for x in before}]
    assert [r['resourceType'] for r in added] == ['AllergyIntolerance', 'MedicationStatement']
    assert len(before) == 3 and len(after) == 5
    assert counts[0]['error'] == 7 and counts[1]['error'] == 9
    assert counts[0]['warning'] == 6 and counts[1]['warning'] == 10
    record = {'repetition': n, 'patient_fhir_demographics': demographic,
        'resource_counts': [len(before), len(after)],
        'validator_counts': [dict(c) for c in counts], 'added_diagnostics': delta,
        'condition_status': [condition(x)['clinicalStatus']['coding'][0]['code']
                             for x in (before, after)],
        'added_resources': added,
        'input_sha256': {str(f.relative_to(d)): hashlib.sha256(f.read_bytes()).hexdigest()
                          for f in d.rglob('*.json')}}
    out['repetitions'].append(record)

# The source observations identify fields/publishing construction, not delivered
# Kafka records. Keep that distinction in both manuscript and response to review.
paths = [
 'backend/src/main/java/com/roberthevesi/cryptoshred_health/dto/PatientVisitEventDto.java',
 'backend/src/main/java/com/roberthevesi/cryptoshred_health/service/EventLogPublisher.java',
 'backend/src/main/java/com/roberthevesi/cryptoshred_health/service/PatientService.java',
 'backend/src/main/java/com/roberthevesi/cryptoshred_health/service/PatientVisitService.java',
 'backend/src/main/java/com/roberthevesi/cryptoshred_health/service/ErasureService.java',
]
out['source_review'] = {
 'scope': 'DTO, creation and erasure event builders and publisher; no Kafka topic consumption',
 'observations': [
  'Creation events include encryptedDataBlob, wrappedDek and iv.',
  'Creation and erasure events retain patientId, eventType, vaultKeyName and timestamp in JSON.',
  'Erasure events omit the encrypted payload; publication is asynchronous.',
  'A retained event identifier remains linkable metadata; key destruction cannot remove it.',
 ],
 'source_sha256': {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in paths},
}
output = ROOT / 'evidence' / 'paired-analysis.json'
output.write_text(json.dumps(out, indent=2) + '\n')
print('Retained-output analysis verified across three repetitions:', output)
