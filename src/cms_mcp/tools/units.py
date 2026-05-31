from __future__ import annotations

from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.endpoints import build_path, compact_query
from cms_mcp.tools.common import compact_result


async def cms_list_units(
    config: CmsMcpConfig,
    *,
    page: int = 1,
    page_size: int = 50,
    supplier: str | None = None,
    inventory_id: str | None = None,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        "/units/list",
        query=compact_query(
            {
                "page": page,
                "pageSize": page_size,
                "supplier": supplier,
                "inventoryId": inventory_id,
            }
        ),
        schema_status="confirmed_live",
    )


async def cms_list_units_by_supplier(
    config: CmsMcpConfig,
    *,
    supplier: str,
    include_rows: bool = False,
    sample_size: int = 20,
) -> dict[str, Any]:
    result = await CmsClient(config).get(
        "/units",
        query=compact_query({"supplier": supplier}),
        schema_status="confirmed_live_supplier_required",
    )
    return compact_result(result, limit=sample_size, include_rows=include_rows)


async def cms_search_units(
    config: CmsMcpConfig,
    *,
    page: int = 1,
    page_size: int = 50,
    project_code: str | None = None,
    publisher_id: str | None = None,
    app_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    tenant_code: str | None = None,
    search_type: str | None = None,
    search_value: str | None = None,
) -> dict[str, Any]:
    body = compact_query(
        {
            "page": page,
            "pageSize": page_size,
            "businessCategoryCode": project_code,
            "publisherId": publisher_id or app_id,
            "os": os,
            "positionId": position_id,
            "tenantCode": tenant_code,
            "searchType": search_type,
            "searchValue": search_value,
        }
    )
    return await CmsClient(config).post_read("/units/search", body=body)


async def cms_get_unit(
    config: CmsMcpConfig,
    *,
    unit_id: str,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/units/{id}", id=unit_id),
        schema_status="confirmed_live",
    )


async def cms_get_unit_history(
    config: CmsMcpConfig,
    *,
    unit_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    return await CmsClient(config).get(
        build_path("/units/{id}/histories", id=unit_id),
        query=compact_query({"startDate": start_date, "endDate": end_date}),
    )


async def cms_list_ssps(config: CmsMcpConfig) -> dict[str, Any]:
    return await CmsClient(config).get("/units/ssps")
