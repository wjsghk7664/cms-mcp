from __future__ import annotations

import asyncio
import shutil
import time
from typing import Any
from urllib.parse import quote, urlparse

from .auth import auth_status
from .config import CmsMcpConfig
from .cookie_store import CookieStore
from .errors import CmsMcpError, ErrorCode


def login_url(config: CmsMcpConfig) -> str:
    return_to = quote(f"{config.cms_frontend}/report/guide", safe="")
    return f"{config.api_base}/auth/google?return_to={return_to}"


async def browser_login(
    config: CmsMcpConfig,
    *,
    headed: bool = True,
    timeout_seconds: int = 300,
    force: bool = False,
) -> dict[str, Any]:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise CmsMcpError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Playwright is not installed. Install dependencies and run `python -m playwright install chromium`.",
        ) from exc

    if force and config.auth_profile_dir.exists():
        shutil.rmtree(config.auth_profile_dir)
    config.auth_profile_dir.mkdir(parents=True, exist_ok=True)

    store = CookieStore(config)
    deadline = time.monotonic() + timeout_seconds
    last_status: dict[str, Any] | None = None

    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(config.auth_profile_dir),
            headless=not headed,
        )
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(login_url(config), wait_until="domcontentloaded")

            while time.monotonic() < deadline:
                cookies = _filter_cookies(await context.cookies(), config)
                if cookies:
                    store.save(cookies)
                    last_status = await auth_status(config)
                    if last_status.get("ok"):
                        return {
                            "ok": True,
                            "env": config.env,
                            "cookie_file": str(config.cookie_file),
                            "profile_dir": str(config.auth_profile_dir),
                            "status": last_status,
                        }
                await asyncio.sleep(2)
        finally:
            await context.close()

    raise CmsMcpError(
        code=ErrorCode.AUTH_REQUIRED,
        message="Timed out waiting for CMS login to complete",
        details={
            "env": config.env,
            "cookie_file": str(config.cookie_file),
            "last_status": last_status,
        },
    )


def _filter_cookies(cookies: list[dict[str, Any]], config: CmsMcpConfig) -> list[dict[str, Any]]:
    allowed_hosts = {
        urlparse(config.api_base).hostname or "",
        urlparse(config.cms_frontend).hostname or "",
    }
    filtered: list[dict[str, Any]] = []
    for cookie in cookies:
        domain = str(cookie.get("domain") or "").lstrip(".")
        if not domain:
            continue
        if any(_domain_matches(host, domain) for host in allowed_hosts):
            filtered.append(cookie)
    return filtered


def _domain_matches(host: str, cookie_domain: str) -> bool:
    if not host or not cookie_domain:
        return False
    return host == cookie_domain or host.endswith("." + cookie_domain)

