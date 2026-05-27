# CMS MCP Live Validation

Date: 2026-05-27

Environment: prod

Validation command:

```bash
cms-mcp smoke --env prod --target catalog
```

Result: passed.

The stronger command below was also run:

```bash
cms-mcp smoke --env prod --target all
```

Result: passed. `catalog` and `all` both pass with automatic ID selection.

## Confirmed Auth

| Check | Result |
| --- | --- |
| local cookie file exists | OK |
| `/users/me` | OK |
| `/inventories/projects` auth probe | OK |

Sensitive values were redacted from CLI output.

## Confirmed Endpoint Shapes

| Tool | Endpoint | Result shape |
| --- | --- | --- |
| `cms_me` | `/users/me` | dict with `id`, `name`, `email`, `role`, `isFirstLogin`, default project/publisher |
| `cms_list_users` | `/users` | dict with `data`, `total`; row keys include `id`, `name`, `email`, `role`, `roleLastRequestedAt`, `roleLastUpdatedAt` |
| `cms_get_user_default_settings` | `/users/default-settings` | dict with `defaultSettings` |
| `cms_dimensions` | multiple dimension endpoints | dict with confirmed master data targets: `countries`, `currencies`, `formats`, `locations`, `os`, `platforms`, `projects`, `publishers`, `screens`, `sizes`, `ssps`, `tenants` |
| `cms_list_ssps` | `/units/ssps` | list, first item keys `code`, `name` |
| `cms_report_metadata` | `/cms/business-categories`, `/cms/publishers`, `/cms/positions` | dict with `businessCategories`, `publishers`, `positions` |
| `cms_list_inventories` | `/inventories` | dict with `data`, `total`; row keys include `id`, `project`, `publisher`, `screen`, `location`, `platform`, `tenant`, `mediationStatus` |
| `cms_search_units` | `/units/search` | dict with `data`, `total`; row keys `inventory`, `unit` |
| `cms_export_units_csv` | `/units/search` | client-side CSV dict with `filename`, `content_type`, `row_count`, `csv` |
| `cms_list_units` | `/units/list` | dict with `data`, `total`; row keys include `id`, `inventoryId`, `supplier`, `format`, `size`, `label`, `positionName`, `isReporting` |
| `cms_list_units_by_supplier` | `/units` | list of supplier units; default tool output is compacted unless `include_rows=true` |
| `cms_report_columns` | `/cms/stats/columns`, `/cms/stats/column-presets`, `/cms/stats/column-settings/me` | dict with `columns`, `presets`, `settings` |
| `cms_report_sales` | `/cms/revenues` | dict with `dataByPlatform`, `totalStat` |
| `cms_export_sales_csv` | `/cms/revenues` | client-side CSV dict with `filename`, `content_type`, `row_count`, `csv` |
| `cms_report_period` | `/cms/reports/kpi` | dict with `data`, `status`; row keys include `date`, `dau`, `firstLook`, `impression`, `revenue` |
| `cms_export_period_csv` | `/cms/reports/kpi` | client-side CSV dict with `filename`, `content_type`, `row_count`, `csv` |
| `cms_report_kpi` | `/cms/reports/kpi` | same as `cms_report_period` |
| `cms_report_adnetworks` | `/cms/stats` | dict with `data`, `total`; rows include `children`, `id`, `name`, `os`, `stats`, `type` |
| `cms_report_adnetwork_ssp` | `/cms/stats/ssp/{id}` | dict with `data`, `total`; rows are date-level SSP metrics |
| `cms_report_adnetwork_unit` | `/cms/stats/ad-network-unit/{id}` | dict with `data`, `total`, `inventoryId`, `supplierUnitId`, `unitId` |
| `cms_report_media_unit` | `/cms/stats/media-unit/{id}` | dict with `data`, `total`, `inventoryId`, `supplierUnitId`, `unitId` |
| `cms_list_ads_files` | `/ads-files` | list, first item keys `id`, `platform`, `publisherName` |
| `cms_get_inventory` | `/inventories/{id}` | dict with inventory detail keys |
| `cms_get_inventory_history` | `/inventories/{id}/histories` | dict with `histories`, `inventoryId`, `page`, `pageSize`, `totalCount` |
| `cms_list_inventory_units` | `/inventories/{id}/units` | dict with `unitList` |
| `cms_mediation_requests` | `/cms/inventories/{id}/mediation-requests` | dict with mediation request summary keys |
| `cms_mediation_settings` | `/mediation/inventories/{id}/settings` | dict with `appName`, `backfill`, `count`, `group`, `inventoryId`, `lastUpdatedAt`, `location`, `project`, `screen`, `tenant` |
| `cms_inventory_groups` | `/mediation/inventories/{id}/groups` | dict with `appName`, `backfill`, `count`, `location`, `mediationGroups`, `project`, `screen`, `tenant` for mediation-enabled inventories |
| `cms_get_unit` | `/units/{id}` | dict with unit detail keys including `id`, `inventoryId`, `supplier`, `format`, `size`, `label`, `options` |
| `cms_get_unit_history` | `/units/{id}/histories` | dict with `histories`, `unitId` |
| `cms_get_ads_file` | `/ads-files/{id}` | dict with ads-file detail keys including `url`, `fileUrl` |
| `cms_check_ads_file_status` | `/ads-files/{id}/status` | dict with `status` |
| `cms_get_ads_file_history` | `/ads-files/{id}/histories` | dict with `data`, `total` |
| `cms_sdk_init_configs` | `/mediation/sdk-init-configs` | dict with `project`, `ssps` |

## Parameter Corrections From Live Probe

### `/users`

Requires `approvalStatus`.

Confirmed working query patterns:

```text
GET /users?approvalStatus=APPROVED&page=1&pageSize=10
GET /users?approvalStatus=WAIT&page=1&pageSize=10
```

Important:

- Only `APPROVED` and `WAIT` are accepted.
- Tool output redacts email fields.
- `/users/default-settings` works without parameters.
- `/users/first-login` is present in the frontend bundle, but prod returned 500 for a standalone GET, so it is not exposed as an MCP tool.

### `/cms/stats`

The initial inferred query used `startDate`, `endDate`, and `tPositionId`. Live API rejected those.

Confirmed working query pattern:

```text
GET /cms/stats?date=YYYY-MM-DD&businessCategoryId=7&publisherId=1&os=ALL&positionId=all
```

Important:

- `date` must be a valid ISO date string.
- `startDate` and `endDate` are rejected.
- `tPositionId` is rejected.
- `positionId` is accepted.

### `/cms/reports/kpi`

This is the confirmed backing endpoint for the period/KPI report.

Confirmed working query pattern:

```text
GET /cms/reports/kpi?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&businessCategoryId=7&publisherId=1&os=ALL&positionId=all
```

CSV exports for sales, period, and unit search are client-side transforms of confirmed JSON APIs. No separate CMS export endpoint was opened.

### `/cms/stats/*/{id}` drill-downs

The drill-down endpoints use the target id in the path and require pagination.

Confirmed working query patterns:

```text
GET /cms/stats/ssp/{id}?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&page=1&pageSize=50
GET /cms/stats/ad-network-unit/{id}?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&page=1&pageSize=50
GET /cms/stats/media-unit/{id}?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&page=1&pageSize=50
```

### `/cms/positions`

Requires `businessCategoryId`.

Confirmed working query pattern:

```text
GET /cms/positions?businessCategoryId=7
```

### `/inventories/apps`

This endpoint is present in the frontend bundle, but standalone prod calls currently fail with a numeric-string validation error. `cms_dimensions(target="all")` excludes `apps` and includes only live-confirmed dimension masters. Use `cms_dimensions(target="apps")` only for explicit investigation.

### `/ads-files`

The initial inferred query used pagination and project filters. Live API rejected those.

Confirmed working query pattern:

```text
GET /ads-files?platform=APP
GET /ads-files?platform=WEB
```

Important:

- `platform` must be `APP` or `WEB`.
- `page` and `pageSize` are rejected.
- `projectId` is rejected.

### `/inventories/{id}/histories`

`startDate` and `endDate` are required. The implementation now defaults missing values to the last 7 days.

Confirmed working query pattern:

```text
GET /inventories/{id}/histories?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD
```

### `/ads-files/{id}/url`

The standalone endpoint returned 404 in prod. The detail endpoint already returns `url` and `fileUrl`, so `cms_get_ads_file_url` now falls back to:

```text
GET /ads-files/{id}
```

### `/mediation/inventories/{id}/groups`

This endpoint is valid for mediation-enabled inventories. It returned 404 for inventories whose `mediationStatus` was false, and succeeded for a mediation-enabled inventory.

Use:

```text
GET /cms/inventories/{id}/mediation-requests
```

for the separate mediation request summary path.

The sibling settings endpoint is also live-confirmed for a mediation-enabled inventory:

```text
GET /mediation/inventories/{id}/settings
```

### `/units` and `/units/list`

`/units/list` is the paginated unit table endpoint.

Confirmed working query patterns:

```text
GET /units/list?page=1&pageSize=50
GET /units/list?page=1&pageSize=50&supplier=ADMOB
GET /units/list?page=1&pageSize=50&inventoryId=618
```

`/units` is a supplier-specific endpoint and rejects pagination parameters.

Confirmed working query pattern:

```text
GET /units?supplier=ADMOB
```

Important:

- `/units` requires `supplier`.
- `/units` rejects `page` and `pageSize`.
- `/units/visibility` is present in the frontend bundle, but standalone prod calls returned a numeric-string validation error, so it is not exposed as an MCP tool yet.

### `/units/legacy/currency`

Confirmed working metadata endpoint:

```text
GET /units/legacy/currency
```

This is exposed through `cms_dimensions(target="currencies")` and included in `cms_dimensions(target="all")`.

## Rerun Validation

To rerun validation:

```bash
cms-mcp smoke --env prod --target catalog --inventory-id <id>
cms-mcp smoke --env prod --target catalog --ads-file-id <id>
cms-mcp smoke --env prod --target all
```
