from __future__ import annotations

from datetime import date as date_type
from datetime import timedelta
from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.endpoints import build_path, compact_query
from cms_mcp.errors import CmsMcpError, ErrorCode


def _stats_query(
    *,
    date: str | None,
    start_date: str | None,
    end_date: str | None,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
    name: str | None = None,
    is_last_depth: bool | None = None,
) -> dict[str, Any]:
    resolved_date = date or end_date or start_date
    return compact_query(
        {
            "date": resolved_date,
            "businessCategoryId": business_category_id,
            "publisherId": publisher_id,
            "os": os,
            "positionId": position_id,
            "format": format,
            "name": name,
            "isLastDepth": is_last_depth,
        }
    )


def _drilldown_query(
    *,
    start_date: str | None,
    end_date: str | None,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
    name: str | None = None,
    is_last_depth: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    return compact_query(
        {
            "startDate": start_date,
            "endDate": end_date,
            "businessCategoryId": business_category_id,
            "publisherId": publisher_id,
            "os": os,
            "positionId": position_id,
            "format": format,
            "name": name,
            "isLastDepth": is_last_depth,
            "page": page,
            "pageSize": page_size,
        }
    )


def _yesterday() -> str:
    return (date_type.today() - timedelta(days=1)).isoformat()


def _default_range(
    *,
    start_date: str | None,
    end_date: str | None,
    days: int = 7,
) -> tuple[str, str]:
    resolved_end = end_date or _yesterday()
    end = _parse_iso_date(resolved_end, "end_date")
    if start_date:
        _parse_iso_date(start_date, "start_date")
        resolved_start = start_date
    else:
        resolved_start = (end - timedelta(days=days - 1)).isoformat()
    return resolved_start, resolved_end


def _parse_iso_date(value: str, field: str) -> date_type:
    try:
        return date_type.fromisoformat(value)
    except ValueError as exc:
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Date must use YYYY-MM-DD format",
            details={"field": field, "value": value},
        ) from exc


async def cms_report_sales(
    config: CmsMcpConfig,
    *,
    start_date: str,
    end_date: str,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
) -> dict[str, Any]:
    start_date, end_date = _default_range(
        start_date=start_date,
        end_date=end_date,
        days=1,
    )
    return await CmsClient(config).get(
        "/cms/revenues",
        query=compact_query(
            {
                "startDate": start_date,
                "endDate": end_date,
                "businessCategoryId": business_category_id,
                "publisherId": publisher_id,
                "os": os,
                "positionId": position_id,
            }
        ),
        schema_status="confirmed_live",
    )


async def cms_report_period(
    config: CmsMcpConfig,
    *,
    start_date: str,
    end_date: str,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
) -> dict[str, Any]:
    start_date, end_date = _default_range(
        start_date=start_date,
        end_date=end_date,
    )
    return await cms_report_kpi(
        config,
        start_date=start_date,
        end_date=end_date,
        business_category_id=business_category_id,
        publisher_id=publisher_id,
        os=os,
        position_id=position_id,
    )


async def cms_report_kpi(
    config: CmsMcpConfig,
    *,
    start_date: str,
    end_date: str,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
) -> dict[str, Any]:
    start_date, end_date = _default_range(
        start_date=start_date,
        end_date=end_date,
    )
    return await CmsClient(config).get(
        "/cms/reports/kpi",
        query=compact_query(
            {
                "startDate": start_date,
                "endDate": end_date,
                "businessCategoryId": business_category_id,
                "publisherId": publisher_id,
                "os": os,
                "positionId": position_id,
            }
        ),
        schema_status="confirmed_live",
    )


async def cms_report_adnetworks(
    config: CmsMcpConfig,
    *,
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
) -> dict[str, Any]:
    date = date or end_date or start_date or _yesterday()
    return await CmsClient(config).get(
        "/cms/stats",
        query=_stats_query(
            date=date,
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
        ),
        schema_status="confirmed_live_single_date",
    )


async def cms_report_adnetwork_ssp(
    config: CmsMcpConfig,
    *,
    ssp_id: str,
    start_date: str,
    end_date: str,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
    name: str | None = None,
    is_last_depth: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    start_date, end_date = _default_range(
        start_date=start_date,
        end_date=end_date,
    )
    return await CmsClient(config).get(
        build_path("/cms/stats/ssp/{id}", id=ssp_id),
        query=_drilldown_query(
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
            name=name,
            is_last_depth=is_last_depth,
            page=page,
            page_size=page_size,
        ),
        schema_status="confirmed_live",
    )


async def cms_report_adnetwork_unit(
    config: CmsMcpConfig,
    *,
    adnetwork_unit_id: str,
    start_date: str,
    end_date: str,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
    name: str | None = None,
    is_last_depth: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    start_date, end_date = _default_range(
        start_date=start_date,
        end_date=end_date,
    )
    return await CmsClient(config).get(
        build_path("/cms/stats/ad-network-unit/{id}", id=adnetwork_unit_id),
        query=_drilldown_query(
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
            name=name,
            is_last_depth=is_last_depth,
            page=page,
            page_size=page_size,
        ),
        schema_status="confirmed_live",
    )


async def cms_report_media_unit(
    config: CmsMcpConfig,
    *,
    media_unit_id: str,
    start_date: str,
    end_date: str,
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
    name: str | None = None,
    is_last_depth: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    start_date, end_date = _default_range(
        start_date=start_date,
        end_date=end_date,
    )
    return await CmsClient(config).get(
        build_path("/cms/stats/media-unit/{id}", id=media_unit_id),
        query=_drilldown_query(
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
            name=name,
            is_last_depth=is_last_depth,
            page=page,
            page_size=page_size,
        ),
        schema_status="confirmed_live",
    )


async def cms_report_metadata(
    config: CmsMcpConfig,
    *,
    business_category_id: str | None = None,
) -> dict[str, Any]:
    client = CmsClient(config)
    categories = await client.get("/cms/business-categories")
    publishers = await client.get("/cms/publishers")
    data: dict[str, Any] = {
        "businessCategories": categories["data"],
        "publishers": publishers["data"],
    }
    warnings: list[str] = []
    if business_category_id:
        positions = await client.get(
            "/cms/positions",
            query={"businessCategoryId": business_category_id},
        )
        data["positions"] = positions["data"]
    else:
        warnings.append("Pass business_category_id to include /cms/positions.")

    return {
        "ok": True,
        "env": config.env,
        "source": "cms_api",
        "schema_status": "confirmed_live",
        "data": data,
        "warnings": warnings,
    }


async def cms_report_columns(config: CmsMcpConfig) -> dict[str, Any]:
    client = CmsClient(config)
    columns = await client.get("/cms/stats/columns")
    presets = await client.get("/cms/stats/column-presets")
    settings = await client.get("/cms/stats/column-settings/me")
    return {
        "ok": True,
        "env": config.env,
        "source": "cms_api",
        "schema_status": "confirmed_bundle",
        "data": {
            "columns": columns["data"],
            "presets": presets["data"],
            "settings": settings["data"],
        },
    }
