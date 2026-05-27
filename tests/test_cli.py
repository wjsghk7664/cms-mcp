from __future__ import annotations

import json

from cms_mcp.cli import main


def test_tools_command_prints_registered_tool_catalog(capsys) -> None:
    assert main(["tools"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["count"] == 37
    assert {tool["name"] for tool in payload["tools"]} >= {
        "cms_health",
        "cms_search_units",
        "cms_mediation_settings",
        "cms_export_sales_csv",
    }


def test_codex_config_command_prints_config_block(capsys, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["codex-config", "--env", "prod", "--command", "/tmp/cms-mcp"]) == 0

    output = capsys.readouterr().out
    assert "[mcp_servers.cms_mcp]" in output
    assert 'command = "/tmp/cms-mcp"' in output
    assert f'CMS_MCP_COOKIE_FILE = "{tmp_path}/.cms-mcp/cookies/prod.json"' in output


def test_claude_config_command_prints_config_payload(capsys, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["claude-config", "--env", "prod", "--command", "/tmp/cms-mcp"]) == 0

    payload = json.loads(capsys.readouterr().out)
    server = payload["mcpServers"]["cms_mcp"]
    assert server["command"] == "/tmp/cms-mcp"
    assert server["args"] == ["serve", "--env", "prod"]
    assert server["env"]["CMS_MCP_COOKIE_FILE"] == str(
        tmp_path / ".cms-mcp" / "cookies" / "prod.json"
    )


def test_claude_config_command_installs_all_known_paths(
    capsys,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    variant_dir = tmp_path / "Library" / "Application Support" / "Claude-3p"
    variant_dir.mkdir(parents=True)

    assert main(["claude-config", "--env", "prod", "--install", "--all-known"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["paths"] == [
        str(
            tmp_path
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        ),
        str(variant_dir / "claude_desktop_config.json"),
    ]


def test_mcpb_manifest_command_prints_manifest(capsys, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["mcpb-manifest", "--env", "prod"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "cms-mcp"
    assert payload["server"]["type"] == "uv"
    assert payload["tools_generated"] is False
    assert len(payload["tools"]) == 37
