# CMS MCP

Read-only MCP server for the internal ad CMS.

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

On a fresh Codex, Claude Code, or Claude Desktop device, the one-command setup is:

```bash
mkdir -p ~/workspace && if [ -d ~/workspace/cms-mcp/.git ]; then cd ~/workspace/cms-mcp && git pull; else git clone https://github.com/wjsghk7664/cms-mcp.git ~/workspace/cms-mcp && cd ~/workspace/cms-mcp; fi && ./scripts/setup-codex.sh prod
```

The setup command installs Codex and Claude Code MCP config, then builds and
opens the Claude Desktop extension installer when Claude Desktop is installed.
To refresh Claude Code manually:

```bash
./scripts/install-claude-code.sh prod
```

To reopen the Claude Desktop installer manually:

```bash
./scripts/install-claude-desktop-mcpb.sh prod
```

Claude Desktop will show an extension install dialog. Approve it, then enable
`Cashwalk CMS MCP` from the chat connector menu.

## Auth

Auth is client-managed. MCP tools remain read-only, but by default they verify
the saved CMS session before read API calls. If the session is missing or
expired, the server opens the project-owned login browser, waits for you to
complete CMS Google login, saves fresh cookies, and then continues the original
read. MCP tools never export cookies or call logout.

Disable automatic login prompts with:

```bash
CMS_MCP_AUTO_LOGIN=false cms-mcp serve --env prod
```

```bash
cms-mcp auth login --env prod
cms-mcp auth status --env prod
```

The login command opens a project-owned browser profile, waits for a human to complete CMS Google login, then stores cookies under `.cms-mcp/cookies/{env}.json`.

`auth logout-local` only deletes local `.cms-mcp/` auth state. It does not call CMS `/auth/logout`.

After login, run a sanitized live smoke check:

```bash
cms-mcp smoke --env prod --target basic
cms-mcp smoke --env prod --target catalog
cms-mcp tools
```

## Serve

```bash
cms-mcp serve --env prod
```

The server uses stdio for MCP transport and only calls read-only CMS APIs.

## Query Guidance

For repository or app-scoped questions, treat the requested service name as a
CMS app/publisher filter, not as a project/business-category filter. For
example, to find 한국캐시워크-related inventory, use `app_name="한국캐시워크"`
or a publisher/app id from `cms_report_metadata`, not `project_code`.

To inspect the registered tool names, descriptions, and input schemas without
starting an MCP client:

```bash
cms-mcp tools
cms-mcp mcpb-manifest --env prod
```

## Tools

Current read-only MCP tools:

- `cms_health`
- `cms_me`
- `cms_list_users`
- `cms_get_user_default_settings`
- `cms_dimensions`
- `cms_list_ssps`
- `cms_list_inventories`
- `cms_find_inventory`
- `cms_get_inventory`
- `cms_get_inventory_history`
- `cms_list_inventory_units`
- `cms_list_units`
- `cms_list_units_by_supplier`
- `cms_search_units`
- `cms_export_units_csv`
- `cms_get_unit`
- `cms_get_unit_history`
- `cms_report_sales`
- `cms_export_sales_csv`
- `cms_report_period`
- `cms_export_period_csv`
- `cms_report_kpi`
- `cms_report_adnetworks`
- `cms_report_adnetwork_ssp`
- `cms_report_adnetwork_unit`
- `cms_report_media_unit`
- `cms_report_metadata`
- `cms_report_columns`
- `cms_list_ads_files`
- `cms_get_ads_file`
- `cms_check_ads_file_status`
- `cms_get_ads_file_url`
- `cms_get_ads_file_history`
- `cms_sdk_init_configs`
- `cms_mediation_settings`
- `cms_inventory_groups`
- `cms_mediation_requests`

`cms_inventory_groups` is valid for mediation-enabled inventories. The live smoke auto-selects an inventory whose `mediationStatus` is true when it probes this tool.

## Tests

```bash
python -m pytest
```

More operational detail is in [docs/runbook.md](docs/runbook.md).

Setup on another Codex, Claude Code, or Claude Desktop device is covered in [docs/other-device-setup.md](docs/other-device-setup.md).
