from __future__ import annotations

from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.endpoints import build_path, compact_query
from cms_mcp.errors import CmsMcpError, ErrorCode


async def cms_list_ads_files(
    config: CmsMcpConfig,
    *,
    platform: str | None = None,
    file_type: str | None = None,
) -> dict[str, Any]:
    resolved_platform = platform or file_type
    return await CmsClient(config).get(
        "/ads-files",
        query=compact_query(
            {
                "platform": resolved_platform,
            }
        ),
    )


async def cms_get_ads_file(
    config: CmsMcpConfig,
    *,
    ads_file_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(build_path("/ads-files/{id}", id=ads_file_id))


async def cms_check_ads_file_status(
    config: CmsMcpConfig,
    *,
    ads_file_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/ads-files/{id}/status", id=ads_file_id)
    )


async def cms_get_ads_file_url(
    config: CmsMcpConfig,
    *,
    ads_file_id: str,
) -> dict[str, Any]:
    client = CmsClient(config)
    try:
        return await client.get(build_path("/ads-files/{id}/url", id=ads_file_id))
    except CmsMcpError as exc:
        if exc.code != ErrorCode.UPSTREAM_NOT_FOUND:
            raise
    detail = await client.get(build_path("/ads-files/{id}", id=ads_file_id))
    data = detail.get("data") if isinstance(detail, dict) else None
    if not isinstance(data, dict):
        return detail
    return {
        "ok": True,
        "env": config.env,
        "source": "cms_api",
        "api_base": config.api_base,
        "path": build_path("/ads-files/{id}", id=ads_file_id),
        "schema_status": "fallback_detail_url",
        "data": {
            "id": data.get("id"),
            "url": data.get("url"),
            "fileUrl": data.get("fileUrl"),
            "platform": data.get("platform"),
        },
        "warnings": [
            "/ads-files/{id}/url returned 404 in prod; URL fields were read from /ads-files/{id} instead."
        ],
    }


async def cms_get_ads_file_history(
    config: CmsMcpConfig,
    *,
    ads_file_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/ads-files/{id}/histories", id=ads_file_id)
    )
