from __future__ import annotations

from typing import Any

from cms_mcp.auth import auth_status
from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig


async def cms_health(config: CmsMcpConfig) -> dict[str, Any]:
    return await auth_status(config)


async def cms_me(config: CmsMcpConfig) -> dict[str, Any]:
    return await CmsClient(config).get("/users/me")

