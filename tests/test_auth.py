from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from cms_mcp.auth import auth_status
from cms_mcp.config import CmsMcpConfig
from cms_mcp.cookie_store import CookieStore


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


@pytest.mark.asyncio
async def test_auth_status_missing_cookie(tmp_path: Path) -> None:
    result = await auth_status(make_config(tmp_path))

    assert result["ok"] is False
    assert result["state"] == "MISSING"


@pytest.mark.asyncio
async def test_auth_status_ok(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    CookieStore(config).save(
        [
            {
                "name": "session",
                "value": "secret-value",
                "domain": "ad-manager-api.cashwalk.io",
                "path": "/",
            }
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"id": 1}]})

    result = await auth_status(config, transport=httpx.MockTransport(handler))

    assert result["ok"] is True
    assert result["state"] == "OK"

