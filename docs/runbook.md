# CMS MCP Runbook

Date: 2026-05-27

## Local Setup

```bash
cd /Users/songyooho/workspace/cms-mcp
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

## Login

```bash
cms-mcp auth login --env prod
```

Expected behavior:

- opens a project-owned Chromium profile
- navigates to the CMS Google OAuth entrypoint
- waits for the user to complete login
- writes `.cms-mcp/cookies/prod.json`
- validates the saved cookies against `/users/me` or `/inventories/projects`

The command should not print cookie values.

## Status And Smoke

```bash
cms-mcp auth status --env prod
cms-mcp smoke --env prod --target basic
cms-mcp tools
```

Smoke targets:

| Target | Checks |
| --- | --- |
| `health` | auth probe and `/users/me` |
| `dimensions` | auth probe and project/OS/platform/SSP dimensions |
| `basic` | health plus dimensions |
| `catalog` | sanitized endpoint-shape checks for core read-only tools |
| `all` | catalog plus tentative/legacy read endpoints |

To validate ID-based tools:

```bash
cms-mcp smoke --env prod --target catalog --inventory-id <id>
cms-mcp smoke --env prod --target catalog --ads-file-id <id>
```

`catalog` auto-selects a mediation-enabled inventory when possible, plus a first unit and ads-file id. `all` includes the mediation group probe.

## Serve

```bash
cms-mcp serve --env prod
```

By default, MCP read tools preflight the saved CMS session. If the session is
missing or expired, a local login browser opens, the tool waits for login to
complete, and then the original read continues. To turn that behavior off:

```bash
CMS_MCP_AUTO_LOGIN=false cms-mcp serve --env prod
```

The server uses stdio. stdout is reserved for MCP JSON-RPC messages; operational output should stay out of stdout.

## MCP Client Command

Use this command in MCP client configuration:

```json
{
  "command": "/Users/songyooho/workspace/cms-mcp/.venv/bin/cms-mcp",
  "args": ["serve", "--env", "prod"],
  "cwd": "/Users/songyooho/workspace/cms-mcp"
}
```

## Claude Desktop

Claude Desktop's current local-server flow is a desktop extension (`.mcpb`).
Build and open it from this project directory:

```bash
./scripts/install-claude-desktop-mcpb.sh prod
```

Approve the install dialog in Claude Desktop, then enable `Cashwalk CMS MCP`
from the chat connector menu.

Fallback for older Claude Desktop builds:

```bash
cms-mcp claude-config --env prod --install --all-known
```

Then restart Claude Desktop.

## Read-Only Guarantees

Blocked by tests and runtime guard:

- `PATCH`
- `PUT`
- `DELETE`
- non-whitelisted `POST`
- `/auth/logout`
- `/ads-files/{id}/callback`

Whitelisted read-only POST:

- `/units/search`

## Useful Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest
cms-mcp auth status --env prod
cms-mcp smoke --env prod --target basic
cms-mcp tools
cms-mcp auth logout-local --env prod
cms-mcp auth logout-local --env prod --include-browser-profile
```

`logout-local` deletes local project auth state only. It must not call CMS `/auth/logout`.
