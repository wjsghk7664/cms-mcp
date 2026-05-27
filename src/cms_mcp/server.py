from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .logging import configure_logging
from .tools.ads_txt import (
    cms_check_ads_file_status as _cms_check_ads_file_status,
)
from .tools.ads_txt import (
    cms_get_ads_file as _cms_get_ads_file,
)
from .tools.ads_txt import (
    cms_get_ads_file_history as _cms_get_ads_file_history,
)
from .tools.ads_txt import (
    cms_get_ads_file_url as _cms_get_ads_file_url,
)
from .tools.ads_txt import (
    cms_list_ads_files as _cms_list_ads_files,
)
from .tools.common import tool_result
from .tools.dimensions import cms_dimensions as _cms_dimensions
from .tools.exports import cms_export_period_csv as _cms_export_period_csv
from .tools.exports import cms_export_sales_csv as _cms_export_sales_csv
from .tools.exports import cms_export_units_csv as _cms_export_units_csv
from .tools.health import cms_health as _cms_health
from .tools.health import cms_me as _cms_me
from .tools.inventories import (
    cms_find_inventory as _cms_find_inventory,
)
from .tools.inventories import (
    cms_get_inventory as _cms_get_inventory,
)
from .tools.inventories import (
    cms_get_inventory_history as _cms_get_inventory_history,
)
from .tools.inventories import (
    cms_list_inventories as _cms_list_inventories,
)
from .tools.inventories import (
    cms_list_inventory_units as _cms_list_inventory_units,
)
from .tools.mediation import cms_inventory_groups as _cms_inventory_groups
from .tools.mediation import cms_mediation_requests as _cms_mediation_requests
from .tools.mediation import cms_mediation_settings as _cms_mediation_settings
from .tools.mediation import cms_sdk_init_configs as _cms_sdk_init_configs
from .tools.reports import (
    cms_report_adnetwork_ssp as _cms_report_adnetwork_ssp,
)
from .tools.reports import (
    cms_report_adnetwork_unit as _cms_report_adnetwork_unit,
)
from .tools.reports import (
    cms_report_media_unit as _cms_report_media_unit,
)
from .tools.reports import cms_report_adnetworks as _cms_report_adnetworks
from .tools.reports import cms_report_columns as _cms_report_columns
from .tools.reports import cms_report_kpi as _cms_report_kpi
from .tools.reports import cms_report_metadata as _cms_report_metadata
from .tools.reports import cms_report_period as _cms_report_period
from .tools.reports import cms_report_sales as _cms_report_sales
from .tools.units import cms_get_unit as _cms_get_unit
from .tools.units import cms_get_unit_history as _cms_get_unit_history
from .tools.units import cms_list_units as _cms_list_units
from .tools.units import cms_list_units_by_supplier as _cms_list_units_by_supplier
from .tools.units import cms_list_ssps as _cms_list_ssps
from .tools.units import cms_search_units as _cms_search_units
from .tools.users import cms_get_user_default_settings as _cms_get_user_default_settings
from .tools.users import cms_list_users as _cms_list_users

mcp = FastMCP(
    "Internal CMS Read-Only",
    instructions=(
        "Read-only tools for the internal ad CMS. "
        "This server never creates, updates, deletes, logs out, or starts OAuth."
    ),
)


def _config(env: str | None) -> Any:
    return load_config(env)


@mcp.tool()
async def cms_health(env: str | None = None) -> dict[str, Any]:
    """Check whether saved CMS cookies can access the read-only CMS API."""
    return await tool_result(lambda: _cms_health(_config(env)))


@mcp.tool()
async def cms_me(env: str | None = None) -> dict[str, Any]:
    """Return sanitized current CMS user/session metadata."""
    return await tool_result(lambda: _cms_me(_config(env)))


@mcp.tool()
async def cms_list_users(
    env: str | None = None,
    approval_status: str = "APPROVED",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Read CMS users by approval status. Emails are redacted from tool output."""
    return await tool_result(
        lambda: _cms_list_users(
            _config(env),
            approval_status=approval_status,
            page=page,
            page_size=page_size,
        )
    )


@mcp.tool()
async def cms_get_user_default_settings(env: str | None = None) -> dict[str, Any]:
    """Read the current user's CMS default settings."""
    return await tool_result(lambda: _cms_get_user_default_settings(_config(env)))


@mcp.tool()
async def cms_dimensions(env: str | None = None, target: str = "all") -> dict[str, Any]:
    """Read CMS dimensions such as projects, OS, screens, locations, tenants, and SSPs."""
    return await tool_result(lambda: _cms_dimensions(_config(env), target=target))


@mcp.tool()
async def cms_list_ssps(env: str | None = None) -> dict[str, Any]:
    """Read SSP master data."""
    return await tool_result(lambda: _cms_list_ssps(_config(env)))


@mcp.tool()
async def cms_list_inventories(
    env: str | None = None,
    page: int = 1,
    page_size: int = 50,
    project_code: str | None = None,
    platform: str | None = None,
    os: str | None = None,
    publisher_name: str | None = None,
    position_id: str | None = None,
    tenant_code: str | None = None,
    search_value: str | None = None,
) -> dict[str, Any]:
    """Read inventory rows with CMS filters."""
    return await tool_result(
        lambda: _cms_list_inventories(
            _config(env),
            page=page,
            page_size=page_size,
            project_code=project_code,
            platform=platform,
            os=os,
            publisher_name=publisher_name,
            position_id=position_id,
            tenant_code=tenant_code,
            search_value=search_value,
        )
    )


@mcp.tool()
async def cms_find_inventory(
    env: str | None = None,
    inventory_id: str | None = None,
    project_code: str | None = None,
    platform: str | None = None,
    os: str | None = None,
    screen: str | None = None,
    location: str | None = None,
    page_size: int = 10000,
) -> dict[str, Any]:
    """Find inventory rows by inventory id and optional dimensions."""
    return await tool_result(
        lambda: _cms_find_inventory(
            _config(env),
            inventory_id=inventory_id,
            project_code=project_code,
            platform=platform,
            os=os,
            screen=screen,
            location=location,
            page_size=page_size,
        )
    )


@mcp.tool()
async def cms_get_inventory(env: str | None = None, inventory_id: str = "") -> dict[str, Any]:
    """Read one inventory by id."""
    return await tool_result(
        lambda: _cms_get_inventory(_config(env), inventory_id=inventory_id)
    )


@mcp.tool()
async def cms_get_inventory_history(
    env: str | None = None,
    inventory_id: str = "",
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Read inventory history for a date range."""
    return await tool_result(
        lambda: _cms_get_inventory_history(
            _config(env),
            inventory_id=inventory_id,
            start_date=start_date,
            end_date=end_date,
        )
    )


@mcp.tool()
async def cms_list_inventory_units(
    env: str | None = None,
    inventory_id: str = "",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Read units that belong to an inventory."""
    return await tool_result(
        lambda: _cms_list_inventory_units(
            _config(env),
            inventory_id=inventory_id,
            page=page,
            page_size=page_size,
        )
    )


@mcp.tool()
async def cms_list_units(
    env: str | None = None,
    page: int = 1,
    page_size: int = 50,
    supplier: str | None = None,
    inventory_id: str | None = None,
) -> dict[str, Any]:
    """Read paginated unit rows with optional supplier or inventory filters."""
    return await tool_result(
        lambda: _cms_list_units(
            _config(env),
            page=page,
            page_size=page_size,
            supplier=supplier,
            inventory_id=inventory_id,
        )
    )


@mcp.tool()
async def cms_list_units_by_supplier(
    env: str | None = None,
    supplier: str = "",
    include_rows: bool = False,
    sample_size: int = 20,
) -> dict[str, Any]:
    """Read units from the supplier-specific unit endpoint."""
    return await tool_result(
        lambda: _cms_list_units_by_supplier(
            _config(env),
            supplier=supplier,
            include_rows=include_rows,
            sample_size=sample_size,
        )
    )


@mcp.tool()
async def cms_search_units(
    env: str | None = None,
    page: int = 1,
    page_size: int = 50,
    project_code: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    tenant_code: str | None = None,
    search_type: str | None = None,
    search_value: str | None = None,
) -> dict[str, Any]:
    """Search units using the CMS read-only unit search endpoint."""
    return await tool_result(
        lambda: _cms_search_units(
            _config(env),
            page=page,
            page_size=page_size,
            project_code=project_code,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            tenant_code=tenant_code,
            search_type=search_type,
            search_value=search_value,
        )
    )


@mcp.tool()
async def cms_get_unit(env: str | None = None, unit_id: str = "") -> dict[str, Any]:
    """Read one unit by id."""
    return await tool_result(lambda: _cms_get_unit(_config(env), unit_id=unit_id))


@mcp.tool()
async def cms_get_unit_history(
    env: str | None = None,
    unit_id: str = "",
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Read unit history for a date range."""
    return await tool_result(
        lambda: _cms_get_unit_history(
            _config(env),
            unit_id=unit_id,
            start_date=start_date,
            end_date=end_date,
        )
    )


@mcp.tool()
async def cms_report_sales(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
) -> dict[str, Any]:
    """Read the total sales report."""
    return await tool_result(
        lambda: _cms_report_sales(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
        )
    )


@mcp.tool()
async def cms_export_sales_csv(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    filename: str | None = None,
    max_rows: int = 5000,
) -> dict[str, Any]:
    """Export the total sales report as client-side CSV text."""
    return await tool_result(
        lambda: _cms_export_sales_csv(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            filename=filename,
            max_rows=max_rows,
        )
    )


@mcp.tool()
async def cms_report_adnetworks(
    env: str | None = None,
    date: str | None = None,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    format: str | None = None,
) -> dict[str, Any]:
    """Read the ad-network report."""
    return await tool_result(
        lambda: _cms_report_adnetworks(
            _config(env),
            date=date,
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
        )
    )


@mcp.tool()
async def cms_report_period(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
) -> dict[str, Any]:
    """Read the period report. Parameters still need live schema confirmation."""
    return await tool_result(
        lambda: _cms_report_period(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
        )
    )


@mcp.tool()
async def cms_export_period_csv(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    filename: str | None = None,
    max_rows: int = 5000,
) -> dict[str, Any]:
    """Export the KPI/period report as client-side CSV text."""
    return await tool_result(
        lambda: _cms_export_period_csv(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            filename=filename,
            max_rows=max_rows,
        )
    )


@mcp.tool()
async def cms_report_kpi(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
) -> dict[str, Any]:
    """Read the KPI/period report."""
    return await tool_result(
        lambda: _cms_report_kpi(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
        )
    )


@mcp.tool()
async def cms_export_units_csv(
    env: str | None = None,
    page: int = 1,
    page_size: int = 1000,
    project_code: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    tenant_code: str | None = None,
    search_type: str | None = None,
    search_value: str | None = None,
    filename: str | None = None,
    max_rows: int = 5000,
) -> dict[str, Any]:
    """Export unit search results as client-side CSV text."""
    return await tool_result(
        lambda: _cms_export_units_csv(
            _config(env),
            page=page,
            page_size=page_size,
            project_code=project_code,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            tenant_code=tenant_code,
            search_type=search_type,
            search_value=search_value,
            filename=filename,
            max_rows=max_rows,
        )
    )


@mcp.tool()
async def cms_report_adnetwork_ssp(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    ssp_id: str = "",
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
    """Read the SSP drill-down for the ad-network report."""
    return await tool_result(
        lambda: _cms_report_adnetwork_ssp(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            ssp_id=ssp_id,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
            name=name,
            is_last_depth=is_last_depth,
            page=page,
            page_size=page_size,
        )
    )


@mcp.tool()
async def cms_report_adnetwork_unit(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    adnetwork_unit_id: str = "",
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
    """Read the ad-network-unit drill-down report."""
    return await tool_result(
        lambda: _cms_report_adnetwork_unit(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            adnetwork_unit_id=adnetwork_unit_id,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
            name=name,
            is_last_depth=is_last_depth,
            page=page,
            page_size=page_size,
        )
    )


@mcp.tool()
async def cms_report_media_unit(
    env: str | None = None,
    start_date: str = "",
    end_date: str = "",
    media_unit_id: str = "",
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
    """Read the media-unit drill-down report."""
    return await tool_result(
        lambda: _cms_report_media_unit(
            _config(env),
            start_date=start_date,
            end_date=end_date,
            media_unit_id=media_unit_id,
            business_category_id=business_category_id,
            publisher_id=publisher_id,
            os=os,
            position_id=position_id,
            format=format,
            name=name,
            is_last_depth=is_last_depth,
            page=page,
            page_size=page_size,
        )
    )


@mcp.tool()
async def cms_report_metadata(
    env: str | None = None,
    business_category_id: str | None = None,
) -> dict[str, Any]:
    """Read report filter metadata: business categories, publishers, and optionally positions."""
    return await tool_result(
        lambda: _cms_report_metadata(
            _config(env),
            business_category_id=business_category_id,
        )
    )


@mcp.tool()
async def cms_report_columns(env: str | None = None) -> dict[str, Any]:
    """Read ad-network report column metadata and current column settings."""
    return await tool_result(lambda: _cms_report_columns(_config(env)))


@mcp.tool()
async def cms_list_ads_files(
    env: str | None = None,
    platform: str | None = None,
    file_type: str | None = None,
) -> dict[str, Any]:
    """Read ads.txt or app-ads.txt file records."""
    return await tool_result(
        lambda: _cms_list_ads_files(
            _config(env),
            platform=platform,
            file_type=file_type,
        )
    )


@mcp.tool()
async def cms_get_ads_file(env: str | None = None, ads_file_id: str = "") -> dict[str, Any]:
    """Read one ads.txt or app-ads.txt file record."""
    return await tool_result(
        lambda: _cms_get_ads_file(_config(env), ads_file_id=ads_file_id)
    )


@mcp.tool()
async def cms_check_ads_file_status(
    env: str | None = None,
    ads_file_id: str = "",
) -> dict[str, Any]:
    """Read status for one ads.txt or app-ads.txt file record."""
    return await tool_result(
        lambda: _cms_check_ads_file_status(_config(env), ads_file_id=ads_file_id)
    )


@mcp.tool()
async def cms_get_ads_file_url(
    env: str | None = None,
    ads_file_id: str = "",
) -> dict[str, Any]:
    """Read URL metadata for one ads.txt or app-ads.txt file record."""
    return await tool_result(
        lambda: _cms_get_ads_file_url(_config(env), ads_file_id=ads_file_id)
    )


@mcp.tool()
async def cms_get_ads_file_history(
    env: str | None = None,
    ads_file_id: str = "",
) -> dict[str, Any]:
    """Read history for one ads.txt or app-ads.txt file record."""
    return await tool_result(
        lambda: _cms_get_ads_file_history(_config(env), ads_file_id=ads_file_id)
    )


@mcp.tool()
async def cms_inventory_groups(
    env: str | None = None,
    inventory_id: str = "",
) -> dict[str, Any]:
    """Read mediation groups for an inventory."""
    return await tool_result(
        lambda: _cms_inventory_groups(_config(env), inventory_id=inventory_id)
    )


@mcp.tool()
async def cms_mediation_settings(
    env: str | None = None,
    inventory_id: str = "",
) -> dict[str, Any]:
    """Read mediation settings for a mediation-enabled inventory."""
    return await tool_result(
        lambda: _cms_mediation_settings(_config(env), inventory_id=inventory_id)
    )


@mcp.tool()
async def cms_sdk_init_configs(
    env: str | None = None,
    project: str = "",
    os: str = "",
) -> dict[str, Any]:
    """Read mediation SDK init configs by project and OS."""
    return await tool_result(
        lambda: _cms_sdk_init_configs(_config(env), project=project, os=os)
    )


@mcp.tool()
async def cms_mediation_requests(
    env: str | None = None,
    inventory_id: str = "",
) -> dict[str, Any]:
    """Read mediation requests for an inventory."""
    return await tool_result(
        lambda: _cms_mediation_requests(_config(env), inventory_id=inventory_id)
    )


def run_stdio(env: str | None = None) -> None:
    configure_logging()
    if env:
        os.environ["CMS_MCP_ENV"] = env
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
