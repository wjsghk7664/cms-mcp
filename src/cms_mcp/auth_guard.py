from __future__ import annotations

import asyncio
from typing import Any

from .auth import auth_status
from .browser_auth import browser_login
from .config import CmsMcpConfig
from .errors import CmsMcpError, ErrorCode

_AUTH_LOCKS: dict[str, asyncio.Lock] = {}


async def ensure_authenticated(config: CmsMcpConfig) -> dict[str, Any]:
    status = await auth_status(config)
    if status.get("ok"):
        return {
            "ok": True,
            "env": config.env,
            "action": "already_authenticated",
            "status": status,
        }

    lock = _auth_lock(config)
    async with lock:
        status = await auth_status(config)
        if status.get("ok"):
            return {
                "ok": True,
                "env": config.env,
                "action": "already_authenticated",
                "status": status,
            }

        try:
            login_result = await browser_login(
                config,
                headed=not config.auto_login_headless,
                timeout_seconds=config.auto_login_timeout_seconds,
                force=False,
            )
        except CmsMcpError as exc:
            raise CmsMcpError(
                code=ErrorCode.AUTH_REQUIRED,
                message=(
                    "CMS session is expired or missing. A login window was opened, "
                    "but login did not complete."
                ),
                details={
                    "env": config.env,
                    "cookie_file": str(config.cookie_file),
                    "profile_dir": str(config.auth_profile_dir),
                    "last_status": status,
                    "remediation": f"Run `cms-mcp auth login --env {config.env}`",
                },
            ) from exc

        return {
            "ok": True,
            "env": config.env,
            "action": "login_completed",
            "status": login_result.get("status"),
        }


def _auth_lock(config: CmsMcpConfig) -> asyncio.Lock:
    key = str(config.cookie_file.expanduser().resolve(strict=False))
    lock = _AUTH_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _AUTH_LOCKS[key] = lock
    return lock
