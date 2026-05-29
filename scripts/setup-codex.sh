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

echo "[cms-mcp] installing Claude Code MCP config"
./scripts/install-claude-code.sh "${ENVIRONMENT}"

echo "[cms-mcp] installing Claude Desktop MCP config"
cms-mcp claude-config --env "${ENVIRONMENT}" --install --all-known

echo "[cms-mcp] building Claude Desktop MCPB bundle"
./scripts/build-mcpb.sh "${ENVIRONMENT}"

if [[ -d "/Applications/Claude.app" ]]; then
  echo "[cms-mcp] opening Claude Desktop MCPB installer"
  if open "${ROOT_DIR}/dist/cms-mcp-${ENVIRONMENT}.mcpb"; then
    echo "[cms-mcp] approve the Claude Desktop extension install dialog"
  else
    echo "[cms-mcp] could not open Claude Desktop installer; run ./scripts/install-claude-desktop-mcpb.sh ${ENVIRONMENT}" >&2
  fi
else
  echo "[cms-mcp] Claude Desktop not found at /Applications/Claude.app; skipping MCPB installer open"
fi

echo "[cms-mcp] done. Restart Codex and Claude Code, or open a new session."
echo "[cms-mcp] For Claude Desktop, enable Cashwalk CMS MCP in the chat connector menu after approving the extension install."
