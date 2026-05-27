from __future__ import annotations

from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.endpoints import compact_query
from cms_mcp.errors import CmsMcpError, ErrorCode

APPROVAL_STATUSES = {"APPROVED", "WAIT"}


async def cms_list_users(
    config: CmsMcpConfig,
    *,
    approval_status: str = "APPROVED",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        "/users",
        query=compact_query(
            {
                "approvalStatus": _approval_status(approval_status),
                "page": page,
                "pageSize": page_size,
            }
        ),
        schema_status="confirmed_live_requires_approval_status",
    )


async def cms_get_user_default_settings(config: CmsMcpConfig) -> dict[str, Any]:
    return await CmsClient(config).get(
        "/users/default-settings",
        schema_status="confirmed_live",
    )


def _approval_status(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized not in APPROVAL_STATUSES:
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="approval_status must be APPROVED or WAIT",
            details={"allowed": sorted(APPROVAL_STATUSES)},
        )
    return normalized
