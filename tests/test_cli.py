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
