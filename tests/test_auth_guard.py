from __future__ import annotations

from pathlib import Path

import pytest

from cms_mcp.auth_guard import ensure_authenticated
from cms_mcp.config import CmsMcpConfig


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


@pytest.mark.asyncio
async def test_ensure_authenticated_opens_login_when_status_is_not_ok(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[bool, int]] = []

    async def fake_auth_status(config: CmsMcpConfig) -> dict[str, object]:
        return {"ok": False, "env": config.env, "state": "MISSING"}

    async def fake_browser_login(
        config: CmsMcpConfig,
        *,
        headed: bool,
        timeout_seconds: int,
        force: bool,
    ) -> dict[str, object]:
        calls.append((headed, timeout_seconds))
        return {"ok": True, "status": {"ok": True, "env": config.env}, "force": force}

    monkeypatch.setattr("cms_mcp.auth_guard.auth_status", fake_auth_status)
    monkeypatch.setattr("cms_mcp.auth_guard.browser_login", fake_browser_login)

    result = await ensure_authenticated(make_config(tmp_path))

    assert result["ok"] is True
    assert result["action"] == "login_completed"
    assert calls == [(True, 300)]


@pytest.mark.asyncio
async def test_ensure_authenticated_skips_login_when_status_is_ok(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    async def fake_auth_status(config: CmsMcpConfig) -> dict[str, object]:
        return {"ok": True, "env": config.env, "state": "OK"}

    async def fail_browser_login(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("browser_login should not be called")

    monkeypatch.setattr("cms_mcp.auth_guard.auth_status", fake_auth_status)
    monkeypatch.setattr("cms_mcp.auth_guard.browser_login", fail_browser_login)

    result = await ensure_authenticated(make_config(tmp_path))

    assert result["ok"] is True
    assert result["action"] == "already_authenticated"
