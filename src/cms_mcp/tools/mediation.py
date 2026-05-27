from __future__ import annotations

from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.endpoints import build_path, compact_query


async def cms_inventory_groups(
    config: CmsMcpConfig,
    *,
    inventory_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/mediation/inventories/{id}/groups", id=inventory_id),
        schema_status="confirmed_live_for_mediation_inventory",
    )


async def cms_mediation_settings(
    config: CmsMcpConfig,
    *,
    inventory_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/mediation/inventories/{id}/settings", id=inventory_id),
        schema_status="confirmed_live_for_mediation_inventory",
    )


async def cms_sdk_init_configs(
    config: CmsMcpConfig,
    *,
    project: str,
    os: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        "/mediation/sdk-init-configs",
        query=compact_query({"project": project, "os": os}),
        schema_status="confirmed_live",
    )


async def cms_mediation_requests(
    config: CmsMcpConfig,
    *,
    inventory_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/cms/inventories/{id}/mediation-requests", id=inventory_id),
        schema_status="confirmed_live",
    )
