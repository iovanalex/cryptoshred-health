#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd -- "${SCRIPT_DIR}/../../backend" && pwd)"

cd "${BACKEND_DIR}"

./mvnw -B -ntp \
  -Dtest=FhirExportIntegrationTest,RetentionHorizonIntegrationTest,RetentionPolicyServiceTest,ErasureProofPersistenceTest,WormBackupCryptoShredTest \
  test

