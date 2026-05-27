from __future__ import annotations

from pathlib import Path

from cms_mcp.config import CmsMcpConfig
from cms_mcp.mcpb_bundle import build_mcpb_manifest


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / "workspace" / "cms-mcp" / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path
        / "workspace"
        / "cms-mcp"
        / ".cms-mcp"
        / "browser-profile"
        / "prod",
    )


def test_build_mcpb_manifest_uses_uv_and_local_auth_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    manifest = build_mcpb_manifest(
        make_config(tmp_path),
        [{"name": "cms_health", "description": "Check health"}],
        version="9.9.9",
    )

    assert manifest["manifest_version"] == "0.4"
    assert manifest["version"] == "9.9.9"
    assert manifest["server"]["type"] == "uv"
    assert manifest["server"]["mcp_config"]["args"] == [
        "run",
        "--directory",
        "${__dirname}",
        "cms-mcp",
        "serve",
    ]
    assert manifest["server"]["mcp_config"]["env"]["CMS_MCP_COOKIE_FILE"] == (
        "${HOME}/workspace/cms-mcp/.cms-mcp/cookies/prod.json"
    )
    assert manifest["server"]["mcp_config"]["env"]["CMS_MCP_AUTO_LOGIN"] == "true"
    assert "user_config" not in manifest
    assert manifest["tools"] == [{"name": "cms_health", "description": "Check health"}]
