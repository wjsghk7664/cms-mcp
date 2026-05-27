#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-prod}"
if [[ "${ENVIRONMENT}" != "prod" && "${ENVIRONMENT}" != "test" ]]; then
  echo "Usage: ./scripts/build-mcpb.sh [prod|test]" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE_DIR="${ROOT_DIR}/build/mcpb/cms-mcp-${ENVIRONMENT}"
OUTPUT_DIR="${ROOT_DIR}/dist"
OUTPUT_FILE="${OUTPUT_DIR}/cms-mcp-${ENVIRONMENT}.mcpb"

cd "${ROOT_DIR}"

if [[ ! -x ".venv/bin/cms-mcp" ]]; then
  echo "[cms-mcp] missing .venv/bin/cms-mcp; run ./scripts/setup-codex.sh ${ENVIRONMENT} first" >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "[cms-mcp] npx is required to package MCPB" >&2
  exit 1
fi

rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}" "${OUTPUT_DIR}"

cp -R src "${STAGE_DIR}/src"
cp pyproject.toml README.md "${STAGE_DIR}/"
find "${STAGE_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "${STAGE_DIR}" -type f -name "*.pyc" -delete

.venv/bin/cms-mcp mcpb-manifest --env "${ENVIRONMENT}" --output "${STAGE_DIR}/manifest.json"

npx -y @anthropic-ai/mcpb validate "${STAGE_DIR}/manifest.json"
npx -y @anthropic-ai/mcpb pack "${STAGE_DIR}" "${OUTPUT_FILE}"
npx -y @anthropic-ai/mcpb info "${OUTPUT_FILE}"

echo "[cms-mcp] built ${OUTPUT_FILE}"
