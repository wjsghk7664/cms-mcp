from __future__ import annotations

import json
from pathlib import Path

from cms_mcp.claude_config import install_claude_config, render_claude_config_payload
from cms_mcp.config import CmsMcpConfig


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


def test_render_claude_config_payload_uses_project_auth_paths(tmp_path: Path) -> None:
    payload = render_claude_config_payload(
        make_config(tmp_path),
        command="/tmp/cms-mcp/.venv/bin/cms-mcp",
    )

    server = payload["mcpServers"]["cms_mcp"]
    assert server["command"] == "/tmp/cms-mcp/.venv/bin/cms-mcp"
    assert server["args"] == ["serve", "--env", "prod"]
    assert server["env"]["CMS_MCP_COOKIE_FILE"] == str(
        tmp_path / ".cms-mcp" / "cookies" / "prod.json"
    )


def test_install_claude_config_preserves_existing_json(tmp_path: Path) -> None:
    config_path = tmp_path / "claude_desktop_config.json"
    config_path.write_text(
        json.dumps(
            {
                "preferences": {"sidebarMode": "epitaxy"},
                "mcpServers": {
                    "other": {
                        "command": "/tmp/other",
                        "args": [],
                    },
                    "cms_mcp": {
                        "command": "old",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    result = install_claude_config(
        config_path,
        make_config(tmp_path),
        command="/tmp/new/bin/cms-mcp",
    )
    updated = json.loads(config_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert updated["preferences"] == {"sidebarMode": "epitaxy"}
    assert updated["mcpServers"]["other"]["command"] == "/tmp/other"
    assert updated["mcpServers"]["cms_mcp"]["command"] == "/tmp/new/bin/cms-mcp"
