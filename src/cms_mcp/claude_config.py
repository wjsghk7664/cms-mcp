from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from .config import CmsMcpConfig
from .errors import CmsMcpError, ErrorCode

SERVER_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
CLAUDE_APP_SUPPORT_DIRS = ("Claude", "Claude-3p")


def default_claude_config_path() -> Path:
    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json"
    )


def known_claude_config_paths(*, primary_path: Path | None = None) -> list[Path]:
    candidates = [primary_path or default_claude_config_path()]
    app_support = Path.home() / "Library" / "Application Support"
    for dirname in CLAUDE_APP_SUPPORT_DIRS:
        config_path = app_support / dirname / "claude_desktop_config.json"
        if config_path.parent.exists():
            candidates.append(config_path)
    return _dedupe_paths(candidates)


def build_claude_server_config(
    config: CmsMcpConfig,
    *,
    command: str | None = None,
) -> dict[str, Any]:
    resolved_command = command or str(Path(sys.argv[0]).resolve())
    return {
        "command": resolved_command,
        "args": ["serve", "--env", config.env],
        "env": {
            "CMS_MCP_AUTH_PROFILE_DIR": str(config.auth_profile_dir),
            "CMS_MCP_COOKIE_FILE": str(config.cookie_file),
            "CMS_MCP_LOG_LEVEL": "WARNING",
        },
    }


def render_claude_config_payload(
    config: CmsMcpConfig,
    *,
    server_name: str = "cms_mcp",
    command: str | None = None,
) -> dict[str, Any]:
    _validate_server_name(server_name)
    return {
        "mcpServers": {
            server_name: build_claude_server_config(config, command=command),
        }
    }


def install_claude_config(
    config_path: Path,
    config: CmsMcpConfig,
    *,
    server_name: str = "cms_mcp",
    command: str | None = None,
) -> dict[str, Any]:
    _validate_server_name(server_name)
    payload = _read_json_config(config_path)
    mcp_servers = payload.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        mcp_servers = {}
    mcp_servers[server_name] = build_claude_server_config(config, command=command)
    payload["mcpServers"] = mcp_servers

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "path": str(config_path),
        "server_name": server_name,
    }


def install_known_claude_configs(
    config: CmsMcpConfig,
    *,
    primary_path: Path | None = None,
    server_name: str = "cms_mcp",
    command: str | None = None,
) -> dict[str, Any]:
    results = [
        install_claude_config(
            config_path,
            config,
            server_name=server_name,
            command=command,
        )
        for config_path in known_claude_config_paths(primary_path=primary_path)
    ]
    return {
        "ok": True,
        "server_name": server_name,
        "paths": [result["path"] for result in results],
        "results": results,
    }


def _read_json_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Claude config JSON is invalid",
            details={"path": str(config_path)},
        ) from exc
    if not isinstance(payload, dict):
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Claude config root must be a JSON object",
            details={"path": str(config_path)},
        )
    return payload


def _validate_server_name(server_name: str) -> None:
    if not SERVER_NAME_RE.match(server_name):
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Claude MCP server name must contain only letters, numbers, underscores, and hyphens",
            details={"server_name": server_name},
        )


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    deduped: list[Path] = []
    for path in paths:
        key = str(path.expanduser().resolve(strict=False))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return deduped
