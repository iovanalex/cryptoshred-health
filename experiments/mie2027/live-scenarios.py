#!/usr/bin/env python3
"""HTTP scenarios against an ephemeral CI stack; synthetic data only."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import traceback
import urllib.error
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
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc


def redis(*args):
    return subprocess.check_output(
        ["docker", "exec", "mie-redis", "redis-cli", "--raw", *args], text=True).strip()


def sql(statement):
    return subprocess.check_output(["docker", "exec", "-i",
        os.environ["MIE_POSTGRES_CONTAINER"], "psql", "-U", "root", "-d", "healthdb",
        "-tA", "-v", "ON_ERROR_STOP=1", "-c", statement], text=True).strip()


def vault_status(path, body=None):
    request = urllib.request.Request("http://localhost:8200/v1/" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-Vault-Token": os.environ["VAULT_DEV_ROOT_TOKEN"],
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


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
        RESULTS.append({"scenario": label, "execution": "error", "error": str(exc),
                        "traceback": traceback.format_exc()})
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
    snapshot = api("POST", "/api/backups/export")
    filename = snapshot["fileName"]
    payload = api("GET", "/api/backups/snapshots/" + filename)
    entry = next(v for v in payload["visits"] if v["visitId"] == vid)
    key = entry["vaultKeyName"]
    wrapped = {"ciphertext": entry["wrappedDek"]}
    assert vault_status("transit/decrypt/" + key, wrapped) == 200
    snapshot_path = Path("backend/backups/worm") / filename
    fingerprint = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    save("visit-fhir-before", api("GET", f"/api/patients/{pid}/fhir"))
    proof = api("DELETE", f"/api/erasure/visits/{vid}/forget")
    after = api("GET", f"/api/visits/{vid}")
    remaining = api("GET", f"/api/patients/{pid}")
    save("visit-proof", proof)
    save("visit-fhir-after", api("GET", f"/api/patients/{pid}/fhir"))
    assert after["shredded"] is True
    assert remaining["firstName"] == "SyntheticVISIT"
    assert vault_status("transit/keys/" + key) == 404
    decryption_status = vault_status("transit/decrypt/" + key, wrapped)
    unchanged = hashlib.sha256(snapshot_path.read_bytes()).hexdigest() == fingerprint
    assert decryption_status >= 400
    assert unchanged
    save("worm-snapshot", payload)
    return {"visit_redacted": True, "patient_demographics_retained": True,
            "worm_decrypt_before_http": 200, "worm_decrypt_after_http": decryption_status,
            "vault_key_absent_after": True, "snapshot_bytes_unchanged": unchanged}


def sql_failure():
    p = patient("SQLFAIL")
    pid = p["patientId"]
    key = sql("SELECT k.vault_key_name FROM encryption_keys k JOIN patients p "
              "ON p.encryption_key_id=k.id WHERE p.patient_id='MIE-SQLFAIL'")
    assert vault_status("transit/keys/" + key) == 200
    sql("CREATE FUNCTION mie_reject_update() RETURNS trigger LANGUAGE plpgsql AS $$ "
        "BEGIN IF NEW.patient_id='MIE-SQLFAIL' THEN RAISE EXCEPTION 'MIE injected SQL failure'; "
        "END IF; RETURN NEW; END $$; "
        "CREATE TRIGGER mie_reject_update BEFORE UPDATE ON patients "
        "FOR EACH ROW EXECUTE FUNCTION mie_reject_update()")
    try:
        try:
            api("DELETE", f"/api/erasure/patients/{pid}/forget")
            raise AssertionError("Injected SQL failure did not reject the request")
        except RuntimeError as exc:
            error = str(exc)
            assert "HTTP 500" in error
        state = sql("SELECT shredded, encrypted_data_blob IS NOT NULL FROM patients "
                    "WHERE patient_id='MIE-SQLFAIL'")
        key_status = vault_status("transit/keys/" + key)
        save("sql-failure", {"request_error": error, "sql_state": state,
                             "vault_key_http": key_status})
        assert state == "f|t"
        assert key_status == 404
        return {"sql_rollback_retained_active_ciphertext": True,
                "vault_key_already_destroyed": True, "request_http": 500}
    finally:
        sql("DROP TRIGGER mie_reject_update ON patients; DROP FUNCTION mie_reject_update()")


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
    scenario("S6-sql-failure-after-key-destruction", sql_failure)
    raise SystemExit(1 if any(r["execution"] == "error" for r in RESULTS) else 0)
