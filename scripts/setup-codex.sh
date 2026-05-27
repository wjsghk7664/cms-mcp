#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-prod}"
if [[ "${ENVIRONMENT}" != "prod" && "${ENVIRONMENT}" != "test" ]]; then
  echo "Usage: ./scripts/setup-codex.sh [prod|test]" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$(dirname "${ROOT_DIR}")"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[cms-mcp] project: ${ROOT_DIR}"
echo "[cms-mcp] environment: ${ENVIRONMENT}"

if [[ ! -d ".venv" ]]; then
  echo "[cms-mcp] creating .venv"
  "${PYTHON_BIN}" -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

echo "[cms-mcp] installing package"
python -m pip install -e ".[dev]"

echo "[cms-mcp] installing Playwright Chromium"
python -m playwright install chromium

echo "[cms-mcp] opening CMS login"
cms-mcp auth login --env "${ENVIRONMENT}"

echo "[cms-mcp] checking auth and basic smoke"
cms-mcp auth status --env "${ENVIRONMENT}"
cms-mcp smoke --env "${ENVIRONMENT}" --target basic

echo "[cms-mcp] installing Codex MCP config"
cms-mcp codex-config --env "${ENVIRONMENT}" --install

echo "[cms-mcp] installing Claude Desktop MCP config"
cms-mcp claude-config --env "${ENVIRONMENT}" --install --all-known

echo "[cms-mcp] done. Restart Codex and Claude Desktop, or open a new session."
