from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.endpoints import build_path, compact_query


async def cms_list_inventories(
    config: CmsMcpConfig,
    *,
    page: int = 1,
    page_size: int = 50,
    project_code: str | None = None,
    platform: str | None = None,
    os: str | None = None,
    publisher_name: str | None = None,
    app_name: str | None = None,
    position_id: str | None = None,
    tenant_code: str | None = None,
    search_value: str | None = None,
) -> dict[str, Any]:
    query = compact_query(
        {
            "page": page,
            "pageSize": page_size,
            "projectCode": project_code,
            "platform": platform,
            "os": os,
            "publisherName": publisher_name or app_name,
            "positionId": position_id,
            "tenantCode": tenant_code,
            "searchValue": search_value,
        }
    )
    return await CmsClient(config).get("/inventories", query=query)


async def cms_find_inventory(
    config: CmsMcpConfig,
    *,
    inventory_id: str | None = None,
    project_code: str | None = None,
    app_name: str | None = None,
    platform: str | None = None,
    os: str | None = None,
    screen: str | None = None,
    location: str | None = None,
    page_size: int = 10000,
) -> dict[str, Any]:
    result = await cms_list_inventories(
        config,
        page=1,
        page_size=page_size,
        project_code=project_code,
        app_name=app_name,
        platform=platform,
        os=os,
        search_value=inventory_id,
    )
    rows = _extract_rows(result.get("data"))
    if rows is None:
        return result

    matches = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if inventory_id and str(row.get("id") or row.get("inventoryId") or "") != str(inventory_id):
            continue
        if screen and screen.lower() not in str(row.get("screen") or row.get("screenName") or "").lower():
            continue
        if location and location.lower() not in str(row.get("location") or row.get("locationName") or "").lower():
            continue
        matches.append(row)

    compact = dict(result)
    compact["data"] = {
        "count": len(matches),
        "items": matches,
    }
    return compact


async def cms_get_inventory(
    config: CmsMcpConfig,
    *,
    inventory_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(build_path("/inventories/{id}", id=inventory_id))


async def cms_get_inventory_history(
    config: CmsMcpConfig,
    *,
    inventory_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    if not start_date:
        start_date = (date.today() - timedelta(days=7)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    return await CmsClient(config).get(
        build_path("/inventories/{id}/histories", id=inventory_id),
        query=compact_query({"startDate": start_date, "endDate": end_date}),
    )


async def cms_list_inventory_units(
    config: CmsMcpConfig,
    *,
    inventory_id: str,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/inventories/{id}/units", id=inventory_id),
        query={"page": page, "pageSize": page_size},
    )


def _extract_rows(data: Any) -> list[Any] | None:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "items", "rows", "content", "result"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return None
