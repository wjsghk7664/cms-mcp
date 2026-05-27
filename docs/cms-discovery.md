# Internal CMS Discovery Notes

Date: 2026-05-27

This document captures the pre-build discovery for an MCP server around the internal ad CMS. It combines:

- live CMS UI inspection from the currently open browser tab
- static inspection of the deployed Next.js frontend bundle
- existing `ads-ai` CMS integration code and local route/tool definitions

Do not paste cookie values, OAuth tokens, account emails, VNC passwords, or other secrets into follow-up docs or MCP logs.

## Executive Summary

The CMS is a Next.js/Refine web app titled `통합광고 CMS`, served from `https://ad-cms.cashwalk.io`, with its backend API at `https://ad-manager-api.cashwalk.io`.

The current logged-in UI is organized around:

- `리포트`
  - `광고 지표 가이드`
  - `총 매출 보고서`
  - `기간 보고서`
  - `애드네트워크 별 보고서`
- `운영`
  - `인벤토리 관리`
    - `인벤토리 설정`
    - `유닛 목록 조회`
  - `txt 라인 관리`
    - `app-ads.txt 관리`
    - `ads.txt 관리`

The deployed frontend exposes a much broader API surface than the pages inspected manually. The most important API groups for a first MCP version are:

- auth and user context: `/users/me`, `/auth/logout`, `/auth/google`
- reports: `/cms/revenues`, `/cms/stats`, `/cms/stats/ssp`, `/cms/stats/ad-network-unit`, `/cms/stats/media-unit`
- reporting metadata: `/cms/business-categories`, `/cms/positions`, `/cms/publishers`, `/cms/stats/columns`, `/cms/stats/column-presets`, `/cms/stats/column-settings/me`
- inventory: `/inventories`, `/inventories/{id}`, `/inventories/{id}/units`, `/inventories/{id}/histories`
- unit search and unit metadata: `/units/search`, `/units`, `/units/list`, `/units/{id}`, `/units/{id}/histories`, `/units/ssps`, `/units/formats`, `/units/sizes`, `/units/countries`
- mediation-related inventory data: `/mediation/inventories/{id}/settings`, `/cms/inventories/{id}/mediation-requests`
- ads.txt/app-ads.txt management: `/ads-files`, `/ads-files/{id}`, `/ads-files/{id}/callback`, `/ads-files/{id}/status`, `/ads-files/{id}/url`, `/ads-files/{id}/histories`

Direct API probing from the browser against `https://ad-manager-api.cashwalk.io` was blocked with `net::ERR_BLOCKED_BY_CLIENT`. A local `ads-ai` CMS client probe also could not use saved cookies for most endpoints. Treat response schemas as partially inferred until an authenticated direct probe is available.

## Environments

| Environment | CMS frontend | API backend | Source |
| --- | --- | --- | --- |
| prod | `https://ad-cms.cashwalk.io` | `https://ad-manager-api.cashwalk.io` | frontend bundle and `ads-ai` |
| test | `https://test-ad-cms.cashwalk.io` | `https://test-ad-manager-api.cashwalk.io` | `ads-ai` auth config |

`ads-ai` also defines Selenium/WebDriver endpoints for browser-based auth renewal:

- prod WebDriver: `http://localhost:4444/wd/hub`
- test WebDriver: `http://localhost:4445/wd/hub`

## Auth And Session Model

Observed frontend behavior:

- user check: `GET /users/me`
- logout: `POST /auth/logout`
- login redirect: `/auth/google?return_to={cmsFrontend}/report/guide`
- requests use `credentials: include`

Existing `ads-ai` behavior:

- stores cookies under `data/cms_cookies_{env}.json`
- treats `/inventories/projects` as a lightweight auth probe
- checks cookie freshness by age and by server rejection
- falls back from direct cookie requests to browser fetch when allowed
- provides relogin/VNC helper routes through its local API server

MCP implication: the MCP tools should not own user credentials directly. The `cms-mcp` project should own a separate client-side auth helper that opens a browser, lets the user complete OAuth, stores a local cookie file with strict permissions, and gives the read-only MCP server a validated session file to consume.

## Frontend Data Provider Behavior

The CMS frontend uses a generic data provider pattern:

| Operation | HTTP behavior |
| --- | --- |
| `getList` | `GET {resource}?page=&pageSize=&...` |
| `getList` with `meta.method = "post"` | `POST {resource}` with JSON payload |
| `getOne` | `GET {resource}/{id}` |
| `create` | `POST {resource}` with JSON payload |
| `update` | `PATCH {resource}/{id}` or explicit `meta.requestUrl` |
| `deleteOne` | `DELETE {resource}/{id}` |
| `custom` | arbitrary method/url/payload/query with credentials included |

This is useful for MCP design because list, read, export, and search tools can share a small HTTP client layer.

## UI Function Inventory

### 광고 지표 가이드

Route: `/report/guide`

Confirmed UI:

- table headers: `용어`, `정의`, `측정 기준`, `비고`
- contains metric definitions and a Notion link
- no primary action buttons observed

MCP value:

- expose as documentation lookup if the guide can be fetched statically or scraped
- not a high-priority API integration target

### 총 매출 보고서

Route: `/report/sales`

Confirmed UI:

- breadcrumb: `리포트 > 총 매출 보고서`
- buttons: `초기화`, `검색`, `CSV 다운로드`
- filters:
  - `기간` (`date`)
  - `프로젝트` (`businessCategoryId`)
  - `앱/OS` (`publisherId`, `os`)
  - `영역` (`positionId`)
- table headers include `Date`, `Total Ad Revenue`

Inferred API:

- data/export: `/cms/revenues`
- metadata: `/cms/business-categories`

Suggested MCP tools:

- `cms_report_sales`
- `cms_export_sales_csv`

### 기간 보고서

Route: `/report/period`

Confirmed UI:

- breadcrumb: `리포트 > 기간 보고서`
- buttons: `초기화`, `검색`, `CSV 다운로드`
- filters:
  - `기간`
  - `프로젝트`
  - `앱/OS`
  - `영역`
- table headers include:
  - `날짜`
  - `DAU`
  - `First Look`
  - `First Look/DAU`
  - `Impression(fb)`
  - `First Look Fill Rate`
  - `ARPDAU`
  - `Revenue`

Inferred API:

- data/export: `/cms/stats`
- the frontend route references a logical `CMS.PERIOD` resource; exact backend path should be confirmed by authenticated traffic capture.

Suggested MCP tools:

- `cms_report_period`
- `cms_export_period_csv`

### 애드네트워크 별 보고서

Route: `/report/adnetworks`

Confirmed UI:

- breadcrumb: `리포트 > 애드네트워크 별 보고서`
- buttons: `초기화`, `검색`, `CSV 다운로드`, `컬럼 설정`
- filters:
  - `기간`
  - `프로젝트`
  - `앱/OS`
  - `영역`
  - `포맷`
- table headers include:
  - `AD Network`
  - `FORMAT`
  - `OS`
  - `Request(fb)`
  - `Impression(fb)`
  - `Failure(fb)`
  - `Fill Rate(fb)`
  - `유실률(fb)`
  - `Click(fb)`
  - `Click(ssp)`
  - `CTR(fb)`
  - `Revenue(ssp)`
  - `CPM(fb)`
- expandable/drill-down rows link to `/report/adnetworks/ssp/{id}`
- visible networks included `ADFIT`, `ADMIXER`, `ADMOB`, `ADPIE`, `ADPOPCORN`, `CAULY`, `COUPANG`, `EXELBID`, `IRONSOURCE`, `MAX`, `MOMENTO`, `NIMBUS`, `PERFORMENTO`

Inferred API:

- top-level report: `/cms/stats`
- drill-down by SSP: `/cms/stats/ssp`
- drill-down by ad-network unit: `/cms/stats/ad-network-unit`
- drill-down by media unit: `/cms/stats/media-unit`
- column settings:
  - `/cms/stats/column-settings/me`
  - `/cms/stats/columns`
  - `/cms/stats/column-presets`

Suggested MCP tools:

- `cms_report_adnetworks`
- `cms_report_adnetwork_ssp`
- `cms_report_adnetwork_unit`
- `cms_report_media_unit`
- `cms_report_columns`
- `cms_update_report_column_settings`

### 인벤토리 설정

Route: `/operations/inventory`

Confirmed UI:

- breadcrumb: `운영 > 인벤토리 설정`
- heading: `인벤토리 목록`
- buttons: `초기화`, `검색`, `CSV 다운로드`, `인벤토리 추가`
- row actions: `지표 보기`, `관리`
- filters:
  - `프로젝트` (`businessCategoryCode`)
  - `앱/OS` (`publisherName`, `os`)
  - `영역` (`positionId`)
  - `테넌트` (`tenantCode`)
  - free-text search (`searchValue`) with placeholder `Inventory_ID를 입력하세요`
- table headers:
  - `프로젝트`
  - `PLATFORM`
  - `앱`
  - `OS`
  - `TENANT`
  - `SCREEN`
  - `LOCATION`
  - `미디에이션 상태`
  - `Inventory_ID`
  - `리포트`
  - `설정`

Inferred API:

- list/export: `/inventories`
- detail: `/inventories/{id}`
- inventory units: `/inventories/{id}/units`
- history: `/inventories/{id}/histories`
- metadata:
  - `/inventories/projects`
  - `/inventories/apps`
  - `/inventories/publishers`
  - `/inventories/platforms`
  - `/inventories/screens`
  - `/inventories/locations`
  - `/inventories/tenants`
  - `/inventories/os`

Suggested MCP tools:

- `cms_list_inventories`
- `cms_get_inventory`
- `cms_find_inventory`
- `cms_get_inventory_history`
- `cms_list_inventory_units`
- `cms_inventory_dimensions`

### Inventory Unit Management Detail

Observed route: `/operations/inventory/{inventoryId}/units`

Confirmed UI:

- breadcrumb: `운영 > 인벤토리 설정`
- buttons: `인벤토리 목록`, `인벤토리 수정`, `CSV 다운로드`, `유닛 등록`
- search by `Unit_ID`
- table headers:
  - `Unit_ID`
  - `UNIT명`
  - `SSP`
  - `FORMAT`
  - `SIZE`
  - `TIMEOUT`
  - `PURPOSE`
  - `MEMO`
  - `Nudge_Unit_ID`
  - `미디에이션 상태`
  - `리포팅 여부`
  - `프리로드`
  - `수정`
  - `히스토리`

Inferred API:

- `/inventories/{id}/units`
- `/units/{id}`
- `/units/{id}/histories`
- `/units/visibility`
- `/units/ssps`
- `/units/formats`
- `/units/sizes`
- `/units/legacy/currency`
- `/units/countries`

Suggested MCP tools:

- `cms_list_inventory_units`
- `cms_get_unit`
- `cms_create_unit`
- `cms_update_unit`
- `cms_get_unit_history`
- `cms_unit_dimensions`

Write operations should be gated behind an explicit read-only default and user confirmation.

### 유닛 목록 조회

Route: `/operations/unit-info`

Confirmed UI:

- breadcrumb: `운영 > 인벤토리 관리 > 유닛 목록 조회`
- buttons: `초기화`, `검색`, `CSV 다운로드`
- filters:
  - `프로젝트` (`businessCategoryCode`)
  - `앱/OS` (`publisherId`, `os`)
  - `영역` (`positionId`)
  - `테넌트` (`tenantCode`)
  - `searchType`
  - `searchValue`, placeholder `Unit_ID를 입력하세요`
- table headers:
  - `Inventory_ID`
  - `OS`
  - `UNIT명`
  - `UNIT_ID`
  - `TIMEOUT`
  - `MEMO`
  - `PURPOSE`
  - `프리로드`
  - `NUDGE_UNIT_ID`
  - `마지막 업데이트`

Inferred API:

- unit search: `POST /units/search`
- CSV export: `POST /units/search` with export handling
- metadata:
  - `/inventories/projects`
  - `/inventories/publishers`
  - `/inventories/platforms`
  - `/inventories/screens`
  - `/inventories/locations`
  - `/inventories/tenants`
  - `/inventories/os`

Suggested MCP tools:

- `cms_search_units`
- `cms_export_units_csv`

### app-ads.txt 관리

Route: `/operations/ads-txt-management/app-ads-txt`

Confirmed UI:

- breadcrumb: `운영 > app-ads.txt 관리`
- button: `검색`
- project selector: `projectId`
- tab link to `ads.txt 관리`
- no table rendered before selecting a project

Inferred API:

- `/ads-files`
- `/ads-files/{id}`
- `/ads-files/{id}/callback`
- `/ads-files/{id}/status`
- `/ads-files/{id}/url`
- `/ads-files/{id}/histories`
- frontend also uses `/api/proxy?url=` in the ads.txt common chunk

Suggested MCP tools:

- `cms_list_ads_files`
- `cms_get_ads_file`
- `cms_check_ads_file_status`
- `cms_get_ads_file_history`

Write/callback operations need confirmation and audit logging.

### ads.txt 관리

Route: `/operations/ads-txt-management/ads-txt`

Confirmed UI:

- breadcrumb: `운영 > ads.txt 관리`
- button: `검색`
- project selector: `projectId`
- tab link to `app-ads.txt 관리`
- page description in bundle: web ads.txt line management

Inferred API:

- same `/ads-files` group as app-ads.txt

Suggested MCP tools:

- same as app-ads.txt, with an `ads_file_type` or route-specific parameter

### Mediation Pages

Frontend bundle constants and navigation hints include mediation-related routes and APIs, but direct route navigation returned a not-found-like page for:

- `/operations/mediations`
- `/operations/mediations/history`

Known/inferred APIs:

- `/mediation/inventories/{id}/settings`
- `/cms/inventories/{id}/mediation-requests`
- `ads-ai` also calls `/mediation/inventories/{inventory_id}/groups`
- `ads-ai` also calls `/mediation/sdk-init-configs?project={project}&os={os}`

Status: unconfirmed from live UI crawl. Keep these in the MCP backlog, but validate with authenticated API traffic before exposing write or mutation tools.

## API Catalog

### Auth And Users

| Method | Path | Status | Notes |
| --- | --- | --- | --- |
| GET | `/users/me` | confirmed from bundle | current user/session probe |
| GET | `/users` | confirmed from bundle | user list/admin candidate |
| GET/PATCH candidate | `/users/default-settings` | confirmed from bundle | default user settings |
| GET/PATCH candidate | `/users/first-login` | confirmed from bundle | first-login state |
| POST | `/auth/logout` | confirmed from bundle | logout |
| GET | `/auth/google?return_to=...` | confirmed from bundle and `ads-ai` | OAuth entrypoint |

### Report APIs

| Method | Path | Status | Notes |
| --- | --- | --- | --- |
| GET | `/cms/revenues` | confirmed from sales page bundle | total sales report |
| GET | `/cms/stats` | confirmed from ad-network page bundle | stats/report root |
| GET | `/cms/stats/ssp` | confirmed from bundle | SSP drill-down |
| GET | `/cms/stats/ad-network-unit` | confirmed from bundle | ad-network unit drill-down |
| GET | `/cms/stats/media-unit` | confirmed from bundle | media unit drill-down |
| GET | `/cms/business-categories` | confirmed from bundle | project/category filter |
| GET | `/cms/positions` | confirmed from bundle | position/area filter |
| GET | `/cms/publishers` | confirmed from bundle | publisher/app filter |
| GET | `/cms/reports/kpi` | confirmed from bundle | KPI report candidate |
| GET | `/cms/stats/columns` | confirmed from bundle | column metadata |
| GET | `/cms/stats/column-presets` | confirmed from bundle | recommended column presets |
| GET/PATCH candidate | `/cms/stats/column-settings/me` | confirmed from bundle | current user's column settings |

### Inventory APIs

| Method | Path | Status | Notes |
| --- | --- | --- | --- |
| GET | `/inventories` | confirmed from UI/bundle/`ads-ai` | list inventory; supports pagination and filters |
| POST | `/inventories` | inferred from data provider | create inventory |
| GET | `/inventories/{id}` | inferred from data provider |
| PATCH | `/inventories/{id}` | inferred from data provider |
| DELETE | `/inventories/{id}` | inferred from data provider |
| GET | `/inventories/{id}/histories` | confirmed from bundle/`ads-ai` |
| GET | `/inventories/{id}/units` | confirmed from UI/bundle |
| GET | `/inventories/projects` | confirmed from bundle/`ads-ai` |
| GET | `/inventories/apps` | confirmed from bundle |
| GET | `/inventories/publishers` | confirmed from bundle |
| GET | `/inventories/platforms` | confirmed from bundle/`ads-ai` |
| GET | `/inventories/screens` | confirmed from bundle/`ads-ai` |
| GET | `/inventories/locations` | confirmed from bundle/`ads-ai` |
| GET | `/inventories/tenants` | confirmed from bundle |
| GET | `/inventories/os` | confirmed from bundle/`ads-ai` |

### Unit APIs

| Method | Path | Status | Notes |
| --- | --- | --- | --- |
| GET | `/units` | confirmed from bundle |
| GET | `/units/list` | confirmed from bundle |
| POST | `/units/search` | confirmed from unit-info page bundle | search/list with payload |
| GET | `/units/{id}` | inferred from data provider |
| PATCH | `/units/{id}` | inferred from data provider |
| DELETE | `/units/{id}` | inferred from data provider |
| GET | `/units/{id}/histories` | confirmed from bundle |
| GET/PATCH candidate | `/units/visibility` | confirmed from bundle |
| GET | `/units/ssps` | confirmed from bundle/`ads-ai` |
| GET | `/units/formats` | confirmed from bundle |
| GET | `/units/sizes` | confirmed from bundle |
| GET | `/units/legacy/currency` | confirmed from bundle |
| GET | `/units/countries` | confirmed from bundle |

### Mediation APIs

| Method | Path | Status | Notes |
| --- | --- | --- | --- |
| GET/PATCH candidate | `/mediation/inventories/{id}/settings` | confirmed from bundle | settings candidate |
| GET | `/cms/inventories/{id}/mediation-requests` | confirmed from bundle |
| GET | `/mediation/inventories/{id}/groups` | confirmed from `ads-ai` | current group configuration |
| GET | `/mediation/sdk-init-configs?project={project}&os={os}` | confirmed from `ads-ai` | SDK init config |

### ads.txt APIs

| Method | Path | Status | Notes |
| --- | --- | --- | --- |
| GET | `/ads-files` | confirmed from bundle |
| POST | `/ads-files` | inferred from data provider |
| GET | `/ads-files/{id}` | confirmed from bundle/data provider |
| PATCH | `/ads-files/{id}` | inferred from data provider |
| DELETE | `/ads-files/{id}` | inferred from data provider |
| POST/GET candidate | `/ads-files/{id}/callback` | confirmed from bundle | callback action needs validation |
| GET | `/ads-files/{id}/status` | confirmed from bundle |
| GET | `/ads-files/{id}/url` | confirmed from bundle |
| GET | `/ads-files/{id}/histories` | confirmed from bundle |

## Existing `ads-ai` CMS Integration

The `ads-ai` project already contains a useful implementation base for a CMS MCP.

### Core Files

| File | Role |
| --- | --- |
| `packages/agent/v2/cms_auth.py` | environment URLs, cookie freshness, relogin payloads |
| `packages/agent/v2/cms_remote_browser.py` | Selenium/browser cookie save/restore and browser fetch fallback |
| `packages/agent/v2/cms_client.py` | CMS HTTP client and high-level inventory/mediation helpers |
| `packages/agent/v2/cms_tools.py` | class-based tools for dimensions, inventory search, groups, SSPs, SDK init configs |
| `packages/agent/v2/cms_network_tools.py` | network-centric inventory and history tools |
| `packages/agent/v2/cms_dimension_matcher.py` | Korean/English dimension matching and alias logic |
| `packages/agent/v2/repo_cms_mapping.py` | repo/project/platform aliases |
| `packages/agent/v2/cms_snapshot_store.py` | local per-repo inventory snapshot fallback |
| `apps/api_server/cms_routes.py` | local auth/relogin/VNC helper routes |
| `packages/core/tools/tool_definitions.py` | tool metadata for CMS tools |
| `packages/core/tools/legacy_adapters.py` | registry bridge for class-based CMS tools |

### Existing Tool Surface In `ads-ai`

| Tool | Purpose |
| --- | --- |
| `cms_dimensions` | list OS/platform/project/screen/location dimensions |
| `cms_find_inventory` | find inventory IDs from project/platform/screen/location/user query |
| `cms_inventory_groups` | fetch mediation groups for an inventory |
| `cms_list_ssps` | list SSP master data |
| `cms_sdk_init_configs` | fetch SDK init config by project and OS |
| `cms_inventories_by_network` | find inventories using a target ad network |
| `cms_inventory_history` | fetch recent inventory history plus current group state |

These map well to an MCP v1 read-only surface.

### Useful Existing Patterns

- Validate auth with `/inventories/projects`.
- `ads-ai` has cache patterns, but `cms-mcp` v1 intentionally does not cache CMS API results so reads reflect live CMS state.
- Use snapshots only as a fallback and label stale data clearly.
- Normalize Korean aliases for project/screen/location/platform before calling APIs.
- Keep direct CMS writes out of automated flows unless the user explicitly confirms them.

## Proposed MCP Scope

### V1 Read-Only Tools

| MCP tool | Backing API/source |
| --- | --- |
| `cms_health` | `/users/me`, `/inventories/projects` |
| `cms_dimensions` | `/inventories/os`, `/inventories/platforms`, `/inventories/projects`, `/inventories/screens`, `/inventories/locations`, `/inventories/tenants`, `/units/ssps` |
| `cms_list_inventories` | `/inventories` |
| `cms_find_inventory` | `/inventories` plus dimension matcher |
| `cms_get_inventory` | `/inventories/{id}` |
| `cms_get_inventory_history` | `/inventories/{id}/histories` |
| `cms_list_inventory_units` | `/inventories/{id}/units` |
| `cms_search_units` | `POST /units/search` |
| `cms_get_unit_history` | `/units/{id}/histories` |
| `cms_report_sales` | `/cms/revenues` |
| `cms_report_adnetworks` | `/cms/stats` |
| `cms_report_adnetwork_ssp` | `/cms/stats/ssp` |
| `cms_list_ads_files` | `/ads-files` |
| `cms_get_ads_file_history` | `/ads-files/{id}/histories` |

### V1.5/V2 Mutating Tools

Keep these behind explicit confirmation, strong audit logs, and dry-run support:

- create/update/delete inventory
- create/update/delete unit
- update unit visibility
- update report column settings
- update ads.txt/app-ads.txt records
- run ads-file callback/status actions
- mediation setting changes

## Open Questions

1. Which auth strategy should the MCP use in production: cookie file, browser bridge, or a small local relogin service?
2. Should the first MCP be strictly read-only?
3. Can we capture authenticated network traffic from the CMS UI to confirm exact report query parameters and response schemas?
4. Are `operations/mediations` pages role-gated, removed, or routed differently from current navigation?
5. Should MCP expose CSV export as files, structured JSON, or both?
6. Which projects/environments are allowed by default: prod, test, or explicit selection only?
7. What audit trail is required for any write operation?

## Known Gaps And Verification Tasks

- Direct API calls from the in-app browser to `ad-manager-api.cashwalk.io` were blocked by the client environment.
- Local saved cookies were unavailable or stale for most direct `ads-ai` CMS probes.
- Exact response schemas are not fully confirmed.
- Exact query parameters for several reports are inferred from UI state and frontend resource constants.
- Mediation management pages were not confirmed through direct route navigation.
- ads.txt pages require project selection before table/action discovery.

Before implementing mutation tools, run an authenticated traffic capture or direct cookie-backed probe for every target endpoint.
