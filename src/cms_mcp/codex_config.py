from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from .config import CmsMcpConfig
from .errors import CmsMcpError, ErrorCode

SERVER_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


def render_codex_config_block(
    config: CmsMcpConfig,
    *,
    server_name: str = "cms_mcp",
    command: str | None = None,
) -> str:
    _validate_server_name(server_name)
    resolved_command = command or str(Path(sys.argv[0]).resolve())
    return "\n".join(
        [
            f"[mcp_servers.{server_name}]",
            f"args = {_toml_array(['serve', '--env', config.env])}",
            f"command = {_toml_string(resolved_command)}",
            "startup_timeout_sec = 30",
            "",
            f"[mcp_servers.{server_name}.env]",
            f"CMS_MCP_AUTH_PROFILE_DIR = {_toml_string(str(config.auth_profile_dir))}",
            f"CMS_MCP_COOKIE_FILE = {_toml_string(str(config.cookie_file))}",
            'CMS_MCP_LOG_LEVEL = "WARNING"',
            "",
        ]
    )


def install_codex_config_block(
    config_path: Path,
    block: str,
    *,
    server_name: str = "cms_mcp",
) -> dict[str, Any]:
    _validate_server_name(server_name)
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    updated = _replace_server_sections(original, server_name).rstrip()
    updated = f"{updated}\n\n{block.rstrip()}\n" if updated else f"{block.rstrip()}\n"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    return {
        "ok": True,
        "path": str(config_path),
        "server_name": server_name,
    }


def _replace_server_sections(text: str, server_name: str) -> str:
    escaped = re.escape(server_name)
    for pattern in (
        rf"(?ms)^\[mcp_servers\.{escaped}\.env\]\n.*?(?=^\[|\Z)",
        rf"(?ms)^\[mcp_servers\.{escaped}\]\n.*?(?=^\[|\Z)",
    ):
        text = re.sub(pattern, "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _validate_server_name(server_name: str) -> None:
    if not SERVER_NAME_RE.match(server_name):
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Codex MCP server name must contain only letters, numbers, and underscores",
            details={"server_name": server_name},
        )


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_array(values: list[str]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"
