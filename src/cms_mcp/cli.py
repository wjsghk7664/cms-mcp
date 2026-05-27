from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Any

from .auth import auth_status
from .browser_auth import browser_login
from .claude_config import (
    default_claude_config_path,
    install_claude_config,
    install_known_claude_configs,
    render_claude_config_payload,
)
from .codex_config import install_codex_config_block, render_codex_config_block
from .config import load_config
from .cookie_store import CookieStore
from .errors import CmsMcpError, error_result
from .logging import configure_logging
from .server import run_stdio
from .smoke import run_smoke
from .utils.redaction import redact


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    try:
        if args.command == "serve":
            run_stdio(env=args.env)
            return 0
        if args.command == "auth":
            return asyncio.run(run_auth(args))
        if args.command == "smoke":
            return asyncio.run(run_smoke_command(args))
        if args.command == "tools":
            return asyncio.run(run_tools_command())
        if args.command == "codex-config":
            return run_codex_config_command(args)
        if args.command == "claude-config":
            return run_claude_config_command(args)
    except CmsMcpError as exc:
        print_json(exc.to_tool_result())
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print_json(error_result(exc))
        return 1
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cms-mcp")
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Run the read-only MCP server over stdio")
    serve.add_argument("--env", choices=["prod", "test"], default=None)

    smoke = subparsers.add_parser("smoke", help="Run sanitized live read-only smoke checks")
    smoke.add_argument("--env", choices=["prod", "test"], default=None)
    smoke.add_argument(
        "--target",
        choices=["health", "dimensions", "basic", "catalog", "all"],
        default="health",
    )
    smoke.add_argument("--inventory-id", default=None)
    smoke.add_argument("--ads-file-id", default=None)

    subparsers.add_parser("tools", help="Print the registered MCP tool catalog")

    codex_config = subparsers.add_parser(
        "codex-config",
        help="Print or install a Codex MCP config block",
    )
    codex_config.add_argument("--env", choices=["prod", "test"], default=None)
    codex_config.add_argument("--server-name", default="cms_mcp")
    codex_config.add_argument("--command", dest="server_command", default=None)
    codex_config.add_argument(
        "--config-path",
        default=str(Path.home() / ".codex" / "config.toml"),
    )
    codex_config.add_argument("--install", action="store_true")

    claude_config = subparsers.add_parser(
        "claude-config",
        help="Print or install a Claude Desktop MCP config entry",
    )
    claude_config.add_argument("--env", choices=["prod", "test"], default=None)
    claude_config.add_argument("--server-name", default="cms_mcp")
    claude_config.add_argument("--command", dest="server_command", default=None)
    claude_config.add_argument(
        "--config-path",
        default=str(default_claude_config_path()),
    )
    claude_config.add_argument(
        "--all-known",
        action="store_true",
        help="Install into the default Claude config and existing known Claude variants",
    )
    claude_config.add_argument("--install", action="store_true")

    auth = subparsers.add_parser("auth", help="Manage local CMS auth state")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)

    login = auth_sub.add_parser("login", help="Open a browser and save CMS cookies")
    login.add_argument("--env", choices=["prod", "test"], default=None)
    login.add_argument("--headless", action="store_true", help="Run browser headless")
    login.add_argument("--timeout-seconds", type=int, default=300)
    login.add_argument("--force", action="store_true", help="Recreate the local browser profile")

    refresh = auth_sub.add_parser("refresh", help="Refresh CMS cookies using the local browser profile")
    refresh.add_argument("--env", choices=["prod", "test"], default=None)
    refresh.add_argument("--headless", action="store_true", help="Run browser headless")
    refresh.add_argument("--timeout-seconds", type=int, default=300)
    refresh.add_argument("--force", action="store_true", help="Recreate the local browser profile")

    status = auth_sub.add_parser("status", help="Check saved CMS cookies")
    status.add_argument("--env", choices=["prod", "test"], default=None)

    logout = auth_sub.add_parser("logout-local", help="Delete local auth state only")
    logout.add_argument("--env", choices=["prod", "test"], default=None)
    logout.add_argument("--include-browser-profile", action="store_true")

    return parser


async def run_auth(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "env", None))
    if args.auth_command in {"login", "refresh"}:
        result = await browser_login(
            config,
            headed=not args.headless,
            timeout_seconds=args.timeout_seconds,
            force=args.force,
        )
        print_json(result)
        return 0
    if args.auth_command == "status":
        result = await auth_status(config)
        print_json(result)
        return 0 if result.get("ok") else 1
    if args.auth_command == "logout-local":
        result = CookieStore(config).delete(
            include_browser_profile=args.include_browser_profile
        )
        print_json({"ok": True, "env": config.env, **result})
        return 0
    return 2


async def run_smoke_command(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "env", None))
    result = await run_smoke(
        config,
        target=args.target,
        inventory_id=args.inventory_id,
        ads_file_id=args.ads_file_id,
    )
    print_json(result)
    return 0 if result.get("ok") else 1


async def run_tools_command() -> int:
    from .server import mcp

    tools = await mcp.list_tools()
    print_json(
        {
            "ok": True,
            "count": len(tools),
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in sorted(tools, key=lambda item: item.name)
            ],
        }
    )
    return 0


def run_codex_config_command(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "env", None))
    block = render_codex_config_block(
        config,
        server_name=args.server_name,
        command=args.server_command,
    )
    if args.install:
        result = install_codex_config_block(
            Path(args.config_path),
            block,
            server_name=args.server_name,
        )
        print_json({**result, "block": block})
    else:
        print(block, file=sys.stdout)
    return 0


def run_claude_config_command(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "env", None))
    if args.install:
        if args.all_known:
            result = install_known_claude_configs(
                config,
                primary_path=Path(args.config_path),
                server_name=args.server_name,
                command=args.server_command,
            )
        else:
            result = install_claude_config(
                Path(args.config_path),
                config,
                server_name=args.server_name,
                command=args.server_command,
            )
        print_json(result)
    else:
        print_json(
            render_claude_config_payload(
                config,
                server_name=args.server_name,
                command=args.server_command,
            )
        )
    return 0


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(redact(payload), ensure_ascii=False, indent=2), file=sys.stdout)


if __name__ == "__main__":
    raise SystemExit(main())
