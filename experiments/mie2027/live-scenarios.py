#!/usr/bin/env python3
"""HTTP scenarios against an ephemeral CI stack; synthetic data only."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request

OUT = Path("experiments/mie2027/live-results")
OUT.mkdir(parents=True, exist_ok=True)
TOKEN = None
RESULTS = []


def api(method, path, body=None):
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    request = urllib.request.Request(
        "http://localhost:8080" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def redis(*args):
    return subprocess.check_output(
        ["docker", "exec", "mie-redis", "redis-cli", "--raw", *args], text=True).strip()


def save(name, value):
    (OUT / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")


def patient(label):
    return api("POST", "/api/patients", {
        "patientId": "MIE-" + label,
        "firstName": "Synthetic" + label, "lastName": "Evaluation",
        "dateOfBirth": "1980-01-01", "gender": "Male"})


def scenario(label, action):
    try:
        observations = action()
        RESULTS.append({"scenario": label, "execution": "completed", "observations": observations})
    except Exception as exc:
        RESULTS.append({"scenario": label, "execution": "error", "error": str(exc)})
    finally:
        save("scenario-results", {"commit": os.environ.get("GITHUB_SHA"),
             "evidence_level": "live HTTP with real services", "results": RESULTS})


def patient_erasure():
    p = patient("PATIENT")
    pid = p["patientId"]
    before = api("GET", f"/api/patients/{pid}")
    assert before["firstName"] == "SyntheticPATIENT"
    assert redis("EXISTS", "patient:" + pid) == "1"
    proof = api("DELETE", f"/api/erasure/patients/{pid}/forget")
    after = api("GET", f"/api/patients/{pid}")
    save("patient-proof", proof)
    save("patient-fhir-after", api("GET", f"/api/patients/{pid}/fhir"))
    assert after["shredded"] is True
    assert after["firstName"] == "[SHREDDED]"
    assert redis("EXISTS", "patient:" + pid) == "0"
    return {"retention_before": before.get("retentionStatus"),
            "proof_retention": proof.get("retentionStatus"),
            "request_accepted": True, "api_redacted": True, "cache_removed": True}


def visit_erasure():
    p = patient("VISIT")
    pid = p["patientId"]
    visit = api("POST", "/api/visits", {"patientId": pid,
        "patientName": "SyntheticVISIT Evaluation", "mrn": pid,
        "diagnosis": "Synthetic diagnosis", "medicalNotes": "Synthetic visit notes"})
    vid = visit["id"]
    save("visit-fhir-before", api("GET", f"/api/patients/{pid}/fhir"))
    proof = api("DELETE", f"/api/erasure/visits/{vid}/forget")
    after = api("GET", f"/api/visits/{vid}")
    remaining = api("GET", f"/api/patients/{pid}")
    save("visit-proof", proof)
    save("visit-fhir-after", api("GET", f"/api/patients/{pid}/fhir"))
    assert after["shredded"] is True
    assert remaining["firstName"] == "SyntheticVISIT"
    return {"visit_redacted": True, "patient_demographics_retained": True}


def cache_failure():
    p = patient("CACHE")
    pid = p["patientId"]
    api("GET", f"/api/patients/{pid}")
    assert "SyntheticCACHE" in redis("GET", "patient:" + pid)
    try:
        assert redis("ACL", "SETUSER", "default", "-del") == "OK"
        proof = api("DELETE", f"/api/erasure/patients/{pid}/forget")
        raw = redis("GET", "patient:" + pid)
        after = api("GET", f"/api/patients/{pid}")
        save("cache-failure-proof", proof)
        return {"redis_del_denied": True,
                "plaintext_residual_in_redis": "SyntheticCACHE" in raw,
                "api_redacted": after.get("firstName") == "[SHREDDED]",
                "reported_cache_status": proof.get("layerStatus", {}).get("REDIS_CACHE")}
    finally:
        redis("ACL", "SETUSER", "default", "+del")
        redis("DEL", "patient:" + pid)


if __name__ == "__main__":
    TOKEN = api("POST", "/api/auth/login", {
        "email": "doctor@hospital.com", "password": "Password123!"})["token"]
    scenario("S1-S2-patient-erasure", patient_erasure)
    scenario("S3-visit-erasure", visit_erasure)
    scenario("S4-cache-eviction-denied", cache_failure)
    raise SystemExit(1 if any(r["execution"] == "error" for r in RESULTS) else 0)
