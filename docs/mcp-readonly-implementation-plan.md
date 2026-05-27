# CMS MCP Read-Only Implementation Plan

Date: 2026-05-27

Goal: build a read-only MCP server for the internal ad CMS. This server must expose CMS data to MCP clients without creating, updating, deleting, logging out, or otherwise mutating CMS state.

## Decision

Use Python for v1.

Rationale:

- The existing `ads-ai` CMS integration is already Python and contains useful auth, cookie, dimension, inventory, and mediation helpers.
- The official MCP documentation lists Python and TypeScript as Tier 1 SDKs.
- The official server quickstart supports Python `FastMCP`, `mcp[cli]`, and `httpx`, which maps cleanly to a read-only HTTP API wrapper.
- A Python server lets us port `ads-ai` logic first, then decide later whether a TypeScript rewrite is worth it.

Transport:

- v1: stdio MCP server
- later: optional HTTP transport only if we need a shared service process

## Strict Non-Goals

- No create/update/delete tools.
- No CMS logout tool.
- No ad file callback trigger.
- No mediation setting changes.
- No direct credential ownership inside the MCP server.
- No scraping UI as the primary data path.
- No logging of cookies, OAuth tokens, account emails, raw request headers, or full URLs containing sensitive query values.

## Read-Only Contract

The server should enforce read-only behavior in code, not only by convention.

Allowed methods:

- `GET` for normal read APIs
- `POST` only for explicitly whitelisted read-only search/report endpoints, such as `/units/search`, if the CMS uses POST for querying

Blocked methods:

- `PATCH`
- `PUT`
- `DELETE`
- non-whitelisted `POST`

Blocked paths even if method looks harmless:

- `/auth/logout`
- `/ads-files/{id}/callback`
- any path whose purpose is not proven read-only

All tools should return a clear `AUTH_REQUIRED`, `FORBIDDEN_READONLY`, `UPSTREAM_UNAVAILABLE`, or `SCHEMA_UNCONFIRMED` style error instead of guessing.

## Project Layout

Proposed structure:

```text
cms-mcp/
  pyproject.toml
  README.md
  src/
    cms_mcp/
      __init__.py
      server.py
      config.py
      client.py
      auth.py
      cli.py
      browser_auth.py
      cookie_store.py
      endpoints.py
      errors.py
      schemas.py
      tools/
        health.py
        dimensions.py
        inventories.py
        units.py
        reports.py
        ads_txt.py
      utils/
        redaction.py
        date_ranges.py
        dimension_matcher.py
  tests/
    test_readonly_guard.py
    test_config.py
    test_client.py
    test_tools_inventories.py
    test_tools_units.py
    test_tools_reports.py
    test_redaction.py
  docs/
    cms-discovery.md
    cms-api-catalog.json
    mcp-readonly-implementation-plan.md
```

## Configuration

Use environment variables only. Do not hardcode local user paths.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `CMS_MCP_ENV` | no | `prod` | `prod` or `test` |
| `CMS_MCP_API_BASE` | no | derived from env | override API base |
| `CMS_MCP_COOKIE_FILE` | no | `.cms-mcp/cookies/{env}.json` | path to this project's CMS cookie JSON |
| `CMS_MCP_AUTH_PROFILE_DIR` | no | `.cms-mcp/browser-profile/{env}` | browser profile used by this project's auth CLI |
| `CMS_MCP_TIMEOUT_SECONDS` | no | `30` | upstream request timeout |
| `CMS_MCP_ALLOW_POST_READS` | no | `true` | allow whitelisted read-only POST endpoints |
| `CMS_MCP_LOG_LEVEL` | no | `INFO` | stderr/file logging level |

Suggested env mapping:

- `prod`: `https://ad-manager-api.cashwalk.io`
- `test`: `https://test-ad-manager-api.cashwalk.io`

## Client-Managed Auth Strategy

V1 must be self-contained inside this repository. Do not depend on `ads-ai` being logged in.

The MCP tools remain read-only. Login, cookie storage, refresh, and local cleanup are handled by a client-side auth manager that is invoked as a local CLI:

```text
cms-mcp auth login --env prod
cms-mcp auth status --env prod
cms-mcp auth refresh --env prod
cms-mcp auth logout-local --env prod
```

Auth components:

| Component | Responsibility | Runs during MCP tool call? |
| --- | --- | --- |
| `AuthClient` / `cli.py` | command routing for `auth login`, `auth status`, `auth refresh`, `auth logout-local` | no |
| `BrowserAuth` / `browser_auth.py` | opens a local browser profile and waits for human OAuth completion | no |
| `CookieStore` / `cookie_store.py` | saves/loads/deletes `.cms-mcp/cookies/{env}.json` with `0600` permissions | load only |
| `CmsClient` / `client.py` | attaches saved cookies and calls read-only CMS APIs | yes |
| `ReadOnlyGuard` | blocks mutation methods and risky action paths | yes |

Auth implementation flow:

1. `auth login` launches a local browser profile owned by this project.
2. The browser opens the CMS OAuth URL: `{apiBase}/auth/google?return_to={cmsFrontend}/report/guide`.
3. The user completes Google login manually in the browser.
4. The CLI waits until the browser reaches an authenticated CMS page.
5. The CLI extracts only the cookies needed for `ad-manager-api.cashwalk.io`.
6. Cookies are saved to `.cms-mcp/cookies/{env}.json` with owner-only file permissions.
7. `auth status` probes `/users/me` and `/inventories/projects`.
8. MCP tools read this project's cookie file and perform the same probe before read API calls.
9. If the probe fails and `CMS_MCP_AUTO_LOGIN=true`, the tool opens the project-owned browser profile, waits for human login, saves fresh cookies, and continues the original read.
10. If auto-login is disabled or login times out, tools return `AUTH_REQUIRED` and tell the user to run `cms-mcp auth login --env {env}`.

The MCP server process can trigger the same local browser login guard during
tool execution, but only as an auth repair step before read-only API calls.
Login and refresh are still available as explicit local CLI actions and are not
exposed as separate LLM-callable MCP tools.

`ads-ai` remains useful only as a reference implementation for endpoint behavior and prior auth lessons. It is not a runtime dependency.

## HTTP Client Layer

Build one shared async client:

- `CmsClient.request_json(method, path, query=None, body=None)`
- `CmsClient.get(path, query=None)`
- `CmsClient.post_read(path, body=None, query=None)`
- CSV export tools should reuse confirmed read-only JSON APIs and perform client-side CSV conversion unless a dedicated export response is confirmed.

Responsibilities:

- attach cookies
- enforce read-only guard
- apply timeout
- normalize pagination
- redact errors before returning them to MCP
- map upstream status codes to stable internal errors
- attach `source`, `env`, `api_base`, and `schema_status` metadata to outputs

Do not let individual tools call `httpx` directly.

## Tool Set

### Phase 1: Foundation

| Tool | Backing API | Notes |
| --- | --- | --- |
| `cms_health` | `/users/me`, `/inventories/projects` | session and API health |
| `cms_me` | `/users/me` | sanitized user/session metadata |
| `cms_dimensions` | `/inventories/*`, `/units/ssps` | dimensions for project, OS, platform, screen, location, tenant, SSP |

### Phase 2: Inventory And Unit Core

| Tool | Backing API | Notes |
| --- | --- | --- |
| `cms_list_inventories` | `/inventories` | filterable, paginated |
| `cms_find_inventory` | `/inventories` plus dimension matcher | Korean/English aliases |
| `cms_get_inventory` | `/inventories/{id}` | if confirmed live |
| `cms_get_inventory_history` | `/inventories/{id}/histories` | date-bounded |
| `cms_list_inventory_units` | `/inventories/{id}/units` | inventory detail page |
| `cms_search_units` | `POST /units/search` | read-only POST whitelist |
| `cms_export_units_csv` | `POST /units/search` | client-side CSV transform of search results |
| `cms_get_unit_history` | `/units/{id}/histories` | date-bounded |
| `cms_list_ssps` | `/units/ssps` | SSP master data |

### Phase 3: Reports

| Tool | Backing API | Notes |
| --- | --- | --- |
| `cms_report_sales` | `/cms/revenues` | total sales report |
| `cms_export_sales_csv` | `/cms/revenues` | client-side CSV transform |
| `cms_report_adnetworks` | `/cms/stats` | top-level ad-network report |
| `cms_report_adnetwork_ssp` | `/cms/stats/ssp` | drill-down |
| `cms_report_adnetwork_unit` | `/cms/stats/ad-network-unit` | drill-down |
| `cms_report_media_unit` | `/cms/stats/media-unit` | drill-down |
| `cms_report_period` | `/cms/reports/kpi` | confirmed KPI/period path |
| `cms_export_period_csv` | `/cms/reports/kpi` | client-side CSV transform |
| `cms_report_columns` | `/cms/stats/columns`, `/cms/stats/column-presets`, `/cms/stats/column-settings/me` | read only |

### Phase 4: ads.txt Read Tools

| Tool | Backing API | Notes |
| --- | --- | --- |
| `cms_list_ads_files` | `/ads-files` | project/type filters |
| `cms_get_ads_file` | `/ads-files/{id}` | detail |
| `cms_check_ads_file_status` | `/ads-files/{id}/status` | read-only status |
| `cms_get_ads_file_history` | `/ads-files/{id}/histories` | history |
| `cms_get_ads_file_url` | `/ads-files/{id}/url` | only if safe and confirmed |

### Backlog: Mediation Read Tools

These are useful but should wait until live schemas are confirmed:

- `cms_inventory_groups`: `/mediation/inventories/{id}/groups`
- `cms_sdk_init_configs`: `/mediation/sdk-init-configs?project={project}&os={os}`
- `cms_mediation_requests`: `/cms/inventories/{id}/mediation-requests`

## Input And Output Shape

Every tool should accept narrow, explicit parameters. Avoid "query string blob" inputs.

Common input fields:

- `env`
- `start_date`
- `end_date`
- `project`
- `project_code`
- `publisher_id`
- `os`
- `platform`
- `position_id`
- `tenant_code`
- `inventory_id`
- `unit_id`
- `page`
- `page_size`

Every output should include:

- `ok`
- `env`
- `source`
- `schema_status`
- `data`
- `pagination`, when relevant
- `warnings`, when relevant

For large list/report outputs, default to compact summaries and allow an explicit `include_rows=true` or `limit` input. MCP clients can become noisy fast if a report returns thousands of rows.

## Caching

Do not cache CMS API results in v1. The expected request volume is low, and live CMS state is more valuable than avoiding a small number of repeated reads.

Do not persist CMS business data to disk in v1 unless the user explicitly asks for snapshots.

## Error Model

Use stable error codes:

- `AUTH_REQUIRED`
- `AUTH_STALE`
- `FORBIDDEN_READONLY`
- `UPSTREAM_UNAVAILABLE`
- `UPSTREAM_FORBIDDEN`
- `UPSTREAM_NOT_FOUND`
- `VALIDATION_ERROR`
- `SCHEMA_UNCONFIRMED`
- `RATE_LIMITED`
- `INTERNAL_ERROR`

Tool errors should be actionable and should not expose raw headers, cookies, or full stack traces.

## Testing Strategy

Offline tests first:

- read-only guard blocks all mutation methods
- read-only POST whitelist only allows known query endpoints
- config/env parsing
- cookie loading without logging cookie values
- URL construction and query encoding
- redaction of errors
- tool schema validation
- pagination normalization

Mocked HTTP tests:

- `cms_health`
- dimensions
- inventory listing/search
- unit search
- report query path/parameter construction
- ads.txt read endpoints

Live smoke tests, skipped by default:

- require `CMS_MCP_COOKIE_FILE`
- run only with `CMS_MCP_LIVE=1`
- start with `/users/me` and `/inventories/projects`
- never call mutation endpoints
- print only sanitized summaries

MCP protocol tests:

- server starts over stdio
- tool list is available
- each Phase 1/2 tool can be invoked against mocked client
- logs go to stderr, not stdout, because stdout is reserved for stdio JSON-RPC

## Implementation Milestones

### M0: Repository Bootstrap

Deliverables:

- `pyproject.toml`
- `src/cms_mcp/server.py`
- basic `README.md`
- dev/test commands
- empty tool registry

Done when:

- server starts over stdio
- tests run
- no stdout logging

### M1: Config, Auth, HTTP Client

Deliverables:

- env config
- cookie loader
- read-only guard
- shared `CmsClient`
- sanitized error model

Done when:

- `/users/me` and `/inventories/projects` can be probed in live mode
- all mutation methods are blocked in unit tests

### M2: Dimensions, Inventory, Unit Tools

Deliverables:

- `cms_health`
- `cms_me`
- `cms_dimensions`
- `cms_list_inventories`
- `cms_find_inventory`
- `cms_get_inventory_history`
- `cms_list_inventory_units`
- `cms_search_units`
- `cms_list_ssps`

Done when:

- mocked tests cover all tools
- live smoke confirms at least health and dimensions

### M3: Reports

Deliverables:

- sales report
- ad-network report
- SSP/ad-network-unit/media-unit drill-downs
- column metadata reads
- period report only after path/params are confirmed

Done when:

- date range validation exists
- large result limiting exists
- schemas are documented as confirmed or unconfirmed

### M4: ads.txt Read Tools

Deliverables:

- list/detail/status/history/url read tools
- project/type filters
- no callback tool

Done when:

- callback endpoint is explicitly blocked by tests
- live smoke validates at least list/status if access allows

### M5: Hardening And Client Setup

Deliverables:

- MCP client config examples
- troubleshooting guide
- auth renewal guide
- full tool catalog
- read-only threat model

Done when:

- a new user can configure the server without seeing secrets
- all live probes are opt-in
- all known unconfirmed schemas are labeled

## First Implementation Order

1. Initialize Python project with `uv`.
2. Add `mcp[cli]`, `httpx`, `pydantic`, `pytest`, and an HTTP mocking library.
3. Implement config and redaction first.
4. Implement read-only HTTP client before registering any CMS tool.
5. Add Phase 1 tools.
6. Add mocked tests for Phase 1.
7. Run one live auth smoke with an explicit cookie file.
8. Add Phase 2 tools.
9. Add report tools only after the core inventory/unit layer is stable.

## Acceptance Criteria

The first usable version is done when:

- MCP server starts locally over stdio.
- `cms_health` reports whether the session is usable.
- `cms_dimensions`, `cms_list_inventories`, `cms_find_inventory`, and `cms_search_units` work in mocked tests.
- At least `cms_health` and `cms_dimensions` work in live smoke mode with a valid cookie file.
- All mutation methods and known risky action endpoints are blocked by tests.
- No secret-bearing values are printed to stdout/stderr or returned in tool outputs.
- Tool descriptions clearly say that this MCP is read-only.

## References

- CMS discovery: `docs/cms-discovery.md`
- API catalog: `docs/cms-api-catalog.json`
- Official MCP SDK overview: https://modelcontextprotocol.io/docs/sdk
- Official MCP server guide: https://modelcontextprotocol.io/docs/develop/build-server
