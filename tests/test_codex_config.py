from __future__ import annotations

from pathlib import Path

from cms_mcp.codex_config import install_codex_config_block, render_codex_config_block
from cms_mcp.config import CmsMcpConfig


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


def test_render_codex_config_block_uses_absolute_project_auth_paths(tmp_path: Path) -> None:
    block = render_codex_config_block(
        make_config(tmp_path),
        command="/tmp/cms-mcp/.venv/bin/cms-mcp",
    )

    assert "[mcp_servers.cms_mcp]" in block
    assert 'args = ["serve", "--env", "prod"]' in block
    assert 'command = "/tmp/cms-mcp/.venv/bin/cms-mcp"' in block
    assert f'CMS_MCP_COOKIE_FILE = "{tmp_path}/.cms-mcp/cookies/prod.json"' in block


def test_install_codex_config_block_replaces_existing_server(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                'model = "gpt-5.5"',
                "",
                "[mcp_servers.cms_mcp]",
                'command = "old"',
                "",
                "[mcp_servers.cms_mcp.env]",
                'CMS_MCP_COOKIE_FILE = "old"',
                "",
                "[mcp_servers.node_repl]",
                'command = "node_repl"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    block = render_codex_config_block(
        make_config(tmp_path),
        command="/tmp/new/bin/cms-mcp",
    )

    result = install_codex_config_block(config_path, block)
    updated = config_path.read_text(encoding="utf-8")

    assert result["ok"] is True
    assert 'command = "old"' not in updated
    assert "[mcp_servers.node_repl]" in updated
    assert 'command = "/tmp/new/bin/cms-mcp"' in updated
