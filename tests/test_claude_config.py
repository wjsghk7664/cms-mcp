from __future__ import annotations

import json
from pathlib import Path

from cms_mcp.claude_config import (
    install_claude_config,
    install_known_claude_configs,
    known_claude_config_paths,
    render_claude_config_payload,
)
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


def test_known_claude_config_paths_include_existing_variant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    app_support = tmp_path / "Library" / "Application Support"
    (app_support / "Claude-3p").mkdir(parents=True)

    paths = known_claude_config_paths()

    assert paths == [
        app_support / "Claude" / "claude_desktop_config.json",
        app_support / "Claude-3p" / "claude_desktop_config.json",
    ]


def test_install_known_claude_configs_updates_existing_variant(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    app_support = tmp_path / "Library" / "Application Support"
    variant_config_path = app_support / "Claude-3p" / "claude_desktop_config.json"
    variant_config_path.parent.mkdir(parents=True)
    variant_config_path.write_text(
        json.dumps({"enterpriseConfig": {"enabled": True}}),
        encoding="utf-8",
    )

    result = install_known_claude_configs(
        make_config(tmp_path),
        command="/tmp/cms-mcp/.venv/bin/cms-mcp",
    )
    default_config = json.loads(
        (app_support / "Claude" / "claude_desktop_config.json").read_text(
            encoding="utf-8"
        )
    )
    variant_config = json.loads(variant_config_path.read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["paths"] == [
        str(app_support / "Claude" / "claude_desktop_config.json"),
        str(variant_config_path),
    ]
    assert (
        default_config["mcpServers"]["cms_mcp"]["command"]
        == "/tmp/cms-mcp/.venv/bin/cms-mcp"
    )
    assert variant_config["enterpriseConfig"] == {"enabled": True}
    assert (
        variant_config["mcpServers"]["cms_mcp"]["command"]
        == "/tmp/cms-mcp/.venv/bin/cms-mcp"
    )
