#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${1:?usage: write-provenance.sh OUTPUT_DIRECTORY}"
mkdir -p "${OUTPUT_DIR}"

{
  printf 'evidence_level=%s\n' "${EVIDENCE_LEVEL:-component}"
  printf 'commit=%s\n' "${EVIDENCE_COMMIT:-$(git rev-parse HEAD)}"
  printf 'workflow_run_id=%s\n' "${EVIDENCE_RUN_ID:-local}"
  printf 'workflow_run_attempt=%s\n' "${EVIDENCE_RUN_ATTEMPT:-local}"
  printf 'repetition=%s\n' "${EVIDENCE_REPETITION:-not-applicable}"
  printf 'generated_utc=%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'java_version=%s\n' "$(java -version 2>&1 | head -n 1)"
} > "${OUTPUT_DIR}/provenance.txt"

(
  cd "${OUTPUT_DIR}"
  find . -type f ! -name SHA256SUMS -print0 \
    | sort -z \
    | xargs -0 sha256sum > SHA256SUMS
)

