# CMS MCP Auth Design

Date: 2026-05-27

This project must not depend on `ads-ai` runtime state. `ads-ai` can inform implementation details, but `cms-mcp` must own its own local auth bootstrap, cookie storage, and auth health checks.

## Principle

MCP tools are read-only. Auth setup is client-side and is not exposed as a
standalone MCP tool.

That means:

- LLM-callable tools can read CMS data.
- LLM-callable read tools first validate the saved CMS session.
- If the saved session is missing or expired, read tools can open the local
  project-owned login browser, wait for human Google OAuth completion, save
  fresh cookies, and then continue the original read.
- LLM-callable tools cannot export cookies.
- LLM-callable tools cannot logout of CMS.
- A human-operated local auth client handles browser login, cookie storage, status checks, refresh, and local cleanup.

## Architecture

```text
Human
  |
  v
cms-mcp auth login/status/refresh/logout-local
  |
  +-- BrowserAuth: opens project-owned browser profile
  |
  +-- CookieStore: writes .cms-mcp/cookies/{env}.json
  |
  v
cms-mcp serve
  |
  +-- CookieStore: reads saved cookies
  |
  +-- AuthGuard: validates cookies and opens local login on expiry
  |
  +-- CmsClient: attaches cookies to read-only API calls
  |
  +-- ReadOnlyGuard: blocks mutation methods and action endpoints
  |
  v
CMS API
```

Responsibilities:

| Layer | Owns | Explicitly does not own |
| --- | --- | --- |
| Auth client | browser login, cookie extraction, cookie refresh, local cookie deletion | CMS data tools |
| Cookie store | local session file format, permissions, redaction | password or OAuth secret storage |
| MCP server | read-only tool registration, saved-cookie API calls, automatic local login guard on expired sessions | exporting cookies, logging out, mutating CMS data |
| HTTP client | read-only request execution, retries, errors | direct mutation calls |

This keeps the project self-sufficient while keeping the LLM-callable MCP surface read-only.

## User Flow

First setup:

```bash
cms-mcp auth login --env prod
cms-mcp auth status --env prod
```

Normal MCP use:

```bash
cms-mcp serve --env prod
```

Expired session:

```bash
cms-mcp serve --env prod
```

During MCP use, the first read tool checks the saved session. If the session is
missing or expired, the same project-owned browser profile opens and prompts the
user to log in again. Set `CMS_MCP_AUTO_LOGIN=false` to return `AUTH_REQUIRED`
instead of opening the browser.

Optional local cleanup:

```bash
cms-mcp auth logout-local --env prod
```

`logout-local` deletes this project's local cookie/browser profile. It must not call CMS `/auth/logout`.

## Login Flow

1. Resolve environment:
   - prod CMS: `https://ad-cms.cashwalk.io`
   - prod API: `https://ad-manager-api.cashwalk.io`
   - test CMS: `https://test-ad-cms.cashwalk.io`
   - test API: `https://test-ad-manager-api.cashwalk.io`
2. Launch a Playwright Chromium persistent context with profile dir `.cms-mcp/browser-profile/{env}`.
3. Navigate to `{apiBase}/auth/google?return_to={cmsFrontend}/report/guide`.
4. User completes Google OAuth manually.
5. Wait for a successful CMS page load and/or successful API probe.
6. Extract cookies scoped to the CMS/API domains.
7. Save cookies to `.cms-mcp/cookies/{env}.json`.
8. Set cookie file permissions to owner read/write only.
9. Run `GET /users/me` and `GET /inventories/projects` using the saved cookies.
10. Print a sanitized success/failure summary.

## Client-Side Auth Implementation Plan

### A0: Auth Storage Skeleton

Deliverables:

- `.gitignore` entry for `.cms-mcp/`
- `CookieStore` with save/load/delete/status helpers
- cookie metadata format
- file permission enforcement
- redaction helpers

Done when:

- cookie files are never committed
- tests prove cookie values are not logged
- status works for missing, malformed, and expired-looking files

### A1: Browser Login Client

Deliverables:

- `cms-mcp auth login --env prod|test`
- Playwright persistent profile under `.cms-mcp/browser-profile/{env}`
- OAuth URL construction from env config
- wait loop for authenticated CMS page or API probe
- cookie extraction and storage

Done when:

- user can log in without `ads-ai`
- saved cookies pass `/users/me` or `/inventories/projects`
- CLI output contains only sanitized summaries

### A2: Auth Status And Refresh

Deliverables:

- `cms-mcp auth status`
- `cms-mcp auth refresh`
- stale/missing/invalid session diagnosis

Done when:

- status reports `OK`, `MISSING`, `STALE`, or `REJECTED`
- refresh reuses the project-owned browser profile
- failed refresh tells the user the exact next command

### A3: Local Cleanup

Deliverables:

- `cms-mcp auth logout-local`
- optional `--include-browser-profile`

Done when:

- local cookies can be removed safely
- no CMS `/auth/logout` request is made
- tests prove cleanup only touches project-owned auth paths

## Runtime Flow

The MCP server starts with:

```bash
cms-mcp serve --env prod
```

On startup:

1. Load config.
2. Load `.cms-mcp/cookies/{env}.json` unless `CMS_MCP_COOKIE_FILE` overrides it.
3. Build an HTTP cookie jar.
4. Probe `/users/me` or `/inventories/projects`.
5. If valid, register tools and serve over stdio.
6. If invalid, still start the server but every live tool returns `AUTH_REQUIRED` with remediation instructions.

## CLI Commands

### `cms-mcp auth login`

Human-driven OAuth bootstrap.

Options:

- `--env prod|test`
- `--headed/--headless`; default should be headed
- `--timeout-seconds`
- `--force`; recreate local browser profile

### `cms-mcp auth status`

Checks local cookie freshness without exposing cookie values.

Output:

- env
- API base
- cookie file path
- cookie file exists
- cookie file age
- `/users/me` probe result
- `/inventories/projects` probe result
- sanitized error code if failed

### `cms-mcp auth refresh`

Alias for `auth login` unless a safe silent refresh path is later confirmed.

### `cms-mcp auth logout-local`

Deletes local cookie state and optionally the local browser profile.

It must not call:

- `/auth/logout`
- any CMS mutation/action endpoint

## Cookie Storage

Default paths:

```text
.cms-mcp/
  cookies/
    prod.json
    test.json
  browser-profile/
    prod/
    test/
```

Rules:

- Do not commit `.cms-mcp/`.
- Cookie file permissions should be `0600`.
- Cookie JSON should include metadata: `env`, `created_at`, `api_base`, `cms_frontend`, and `cookies`.
- Never log cookie values.
- Never return cookie values from MCP tools.

## Security Boundary

Keep auth CLI and MCP tools separate:

- CLI can open a browser and write local cookie files.
- MCP tools can only read cookie files and call whitelisted read APIs.
- MCP tools cannot mutate CMS state or local auth state.

This keeps the LLM away from session lifecycle operations while making the project self-sufficient.

## Implementation Notes

Suggested dependencies:

- `mcp[cli]`
- `httpx`
- `pydantic`
- `playwright`

Testing:

- unit test cookie redaction
- unit test missing/stale cookie behavior
- unit test that `/auth/logout` is blocked
- unit test that `logout-local` only deletes local files
- live smoke test gated behind `CMS_MCP_LIVE=1`
