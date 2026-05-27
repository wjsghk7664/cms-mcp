# Other Device Setup

Use this when you want the same CMS MCP server in Codex and Claude Desktop on another Mac.

Do not copy `.cms-mcp/cookies/*.json` or browser profiles between devices. Each device should complete its own CMS login.

## Short Version

On another Mac, run:

```bash
mkdir -p ~/workspace && if [ -d ~/workspace/cms-mcp/.git ]; then cd ~/workspace/cms-mcp && git pull; else git clone https://github.com/wjsghk7664/cms-mcp.git ~/workspace/cms-mcp && cd ~/workspace/cms-mcp; fi && ./scripts/setup-codex.sh prod
```

That one command clones or updates the project, creates `.venv`, installs the package, installs Playwright Chromium, opens CMS login, validates auth, runs a basic smoke check, installs Codex and legacy Claude Desktop MCP configs, builds a Claude Desktop `.mcpb` bundle, and opens the Claude Desktop extension installer when Claude Desktop is installed.

Then restart Codex. If the Claude Desktop install dialog did not open, run:

```bash
./scripts/install-claude-desktop-mcpb.sh prod
```

Approve the extension install dialog in Claude Desktop, then enable `Cashwalk CMS MCP` in the chat connector menu.

## Manual Steps

Use this only if the one-command setup fails.

## 1. Get The Project

Clone the project to the other device. Example:

```bash
mkdir -p ~/workspace
git clone https://github.com/wjsghk7664/cms-mcp.git ~/workspace/cms-mcp
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

## 4. Install MCP Configs

Run this from the project directory on the other device:

```bash
cms-mcp codex-config --env prod --install
cms-mcp claude-config --env prod --install --all-known
./scripts/install-claude-desktop-mcpb.sh prod
```

The first command writes or replaces the `[mcp_servers.cms_mcp]` block in:

```text
~/.codex/config.toml
```

The second command writes or replaces the `mcpServers.cms_mcp` entry in the
default Claude Desktop config and any existing known Claude variant config.
The default path is:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

The third command builds `dist/cms-mcp-prod.mcpb` and opens it in Claude
Desktop's extension installer.

To preview the block before writing it:

```bash
cms-mcp codex-config --env prod
cms-mcp claude-config --env prod
```

## 5. Restart Apps

Restart Codex and Claude Desktop. Then ask:

```text
cms_mcp로 cms_health 확인해줘
```

The server should expose 37 tools.
