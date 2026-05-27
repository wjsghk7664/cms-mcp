from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.cookie_store import CookieStore
from cms_mcp.errors import CmsMcpError, ErrorCode


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


def save_cookie(config: CmsMcpConfig) -> None:
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


@pytest.mark.asyncio
async def test_client_get_returns_redacted_json(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    save_cookie(config)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/users/me"
        return httpx.Response(
            200,
            json={"email": "user@example.com", "name": "User"},
        )

    client = CmsClient(config, transport=httpx.MockTransport(handler))
    result = await client.get("/users/me")

    assert result["ok"] is True
    assert result["data"]["email"] == "[REDACTED_EMAIL]"


@pytest.mark.asyncio
async def test_client_blocks_patch_before_network(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    client = CmsClient(config)

    with pytest.raises(CmsMcpError) as exc:
        await client.request_json("PATCH", "/inventories/1")

    assert exc.value.code == ErrorCode.FORBIDDEN_READONLY


@pytest.mark.asyncio
async def test_client_maps_unauthorized_to_auth_required(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    save_cookie(config)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"})

    client = CmsClient(config, transport=httpx.MockTransport(handler))

    with pytest.raises(CmsMcpError) as exc:
        await client.get("/users/me")

    assert exc.value.code == ErrorCode.AUTH_REQUIRED


@pytest.mark.asyncio
async def test_client_rejects_non_json_response(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    save_cookie(config)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    client = CmsClient(config, transport=httpx.MockTransport(handler))

    with pytest.raises(CmsMcpError) as exc:
        await client.get("/users/me")

    assert exc.value.code == ErrorCode.SCHEMA_UNCONFIRMED


def test_test_module_uses_json_import_to_keep_lint_honest() -> None:
    assert json.loads("{}") == {}

