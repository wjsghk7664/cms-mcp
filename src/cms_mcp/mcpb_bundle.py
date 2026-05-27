from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .config import CmsMcpConfig


def project_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject_path.exists():
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        version_value = payload.get("project", {}).get("version")
        if isinstance(version_value, str):
            return version_value
    return "0.1.0"


def build_mcpb_manifest(
    config: CmsMcpConfig,
    tools: list[dict[str, Any]],
    *,
    version: str | None = None,
) -> dict[str, Any]:
    return {
        "manifest_version": "0.4",
        "name": "cms-mcp",
        "display_name": "Cashwalk CMS MCP",
        "version": version or project_version(),
        "description": "Read-only local MCP server for the internal ad CMS.",
        "long_description": (
            "Provides read-only access to the internal ad CMS from Claude Desktop. "
            "The extension runs locally, uses the CMS cookies saved on this device, "
            "and does not create, update, delete, or log out CMS data."
        ),
        "author": {"name": "Cashwalk Ads"},
        "server": {
            "type": "uv",
            "entry_point": "src/cms_mcp/cli.py",
            "mcp_config": {
                "command": "uv",
                "args": [
                    "run",
                    "--directory",
                    "${__dirname}",
                    "cms-mcp",
                    "serve",
                ],
                "env": {
                    "CMS_MCP_ENV": config.env,
                    "CMS_MCP_COOKIE_FILE": _portable_home_path(config.cookie_file),
                    "CMS_MCP_AUTH_PROFILE_DIR": _portable_home_path(
                        config.auth_profile_dir
                    ),
                    "CMS_MCP_LOG_LEVEL": "WARNING",
                },
            },
        },
        "tools": _manifest_tools(tools),
        "tools_generated": False,
        "keywords": ["cms", "ads", "cashwalk", "read-only", "internal"],
        "compatibility": {
            "platforms": ["darwin"],
            "runtimes": {"python": ">=3.12"},
        },
    }


def _manifest_tools(tools: list[dict[str, Any]]) -> list[dict[str, str]]:
    manifest_tools: list[dict[str, str]] = []
    for tool in sorted(tools, key=lambda item: str(item["name"])):
        manifest_tools.append(
            {
                "name": str(tool["name"]),
                "description": str(tool.get("description") or ""),
            }
        )
    return manifest_tools


def _portable_home_path(path: Path) -> str:
    resolved_path = path.expanduser().resolve(strict=False)
    home = Path.home().resolve(strict=False)
    try:
        return "${HOME}/" + resolved_path.relative_to(home).as_posix()
    except ValueError:
        return str(resolved_path)
