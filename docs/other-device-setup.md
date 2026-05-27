# Other Device Setup

Use this when you want the same CMS MCP server in Codex on another Mac.

Do not copy `.cms-mcp/cookies/*.json` or browser profiles between devices. Each device should complete its own CMS login.

## Short Version

After copying or cloning this project on another Mac, run this from the project directory:

```bash
./scripts/setup-codex.sh prod
```

That one command creates `.venv`, installs the package, installs Playwright Chromium, opens CMS login, validates auth, runs a basic smoke check, and installs the Codex MCP config.

Then restart Codex or open a new Codex session.

## Manual Steps

Use this only if the one-command setup fails.

## 1. Get The Project

Clone or copy the project to the other device. Example path:

```bash
cd ~/workspace/cms-mcp
```

## 2. Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

## 3. Login On That Device

```bash
cms-mcp auth login --env prod
cms-mcp auth status --env prod
cms-mcp smoke --env prod --target basic
```

The cookie file will be created under that device's project directory:

```text
.cms-mcp/cookies/prod.json
```

## 4. Install Codex MCP Config

Run this from the project directory on the other device:

```bash
cms-mcp codex-config --env prod --install
```

This writes or replaces the `[mcp_servers.cms_mcp]` block in:

```text
~/.codex/config.toml
```

To preview the block before writing it:

```bash
cms-mcp codex-config --env prod
```

## 5. Restart Codex

Restart Codex or open a new Codex session. Then ask:

```text
cms_mcp로 cms_health 확인해줘
```

The server should expose 37 tools.
