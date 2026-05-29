#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-prod}"
if [[ "${ENVIRONMENT}" != "prod" && "${ENVIRONMENT}" != "test" ]]; then
  echo "Usage: ./scripts/install-claude-code.sh [prod|test]" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_BIN="${ROOT_DIR}/.venv/bin/cms-mcp"
COOKIE_FILE="${ROOT_DIR}/.cms-mcp/cookies/${ENVIRONMENT}.json"
AUTH_PROFILE_DIR="${ROOT_DIR}/.cms-mcp/browser-profile/${ENVIRONMENT}"

if ! command -v claude >/dev/null 2>&1; then
  echo "[cms-mcp] Claude Code CLI not found; skipping Claude Code MCP install"
  exit 0
fi

if [[ ! -x "${SERVER_BIN}" ]]; then
  echo "[cms-mcp] missing ${SERVER_BIN}; run ./scripts/setup-codex.sh ${ENVIRONMENT} first" >&2
  exit 1
fi

claude mcp remove cms_mcp -s user >/dev/null 2>&1 || true
claude mcp add -s user cms_mcp -- /usr/bin/env \
  "CMS_MCP_COOKIE_FILE=${COOKIE_FILE}" \
  "CMS_MCP_AUTH_PROFILE_DIR=${AUTH_PROFILE_DIR}" \
  "CMS_MCP_AUTO_LOGIN=true" \
  "CMS_MCP_AUTO_LOGIN_TIMEOUT_SECONDS=300" \
  "CMS_MCP_AUTO_LOGIN_HEADLESS=false" \
  "CMS_MCP_LOG_LEVEL=WARNING" \
  "${SERVER_BIN}" serve --env "${ENVIRONMENT}"

claude mcp get cms_mcp
