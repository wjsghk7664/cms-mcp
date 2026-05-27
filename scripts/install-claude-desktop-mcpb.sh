#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-prod}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"${ROOT_DIR}/scripts/build-mcpb.sh" "${ENVIRONMENT}"

BUNDLE_PATH="${ROOT_DIR}/dist/cms-mcp-${ENVIRONMENT}.mcpb"
open "${BUNDLE_PATH}"

echo "[cms-mcp] opened ${BUNDLE_PATH}"
echo "[cms-mcp] In Claude Desktop, approve the extension install and then enable Cashwalk CMS MCP in the chat connectors menu."
