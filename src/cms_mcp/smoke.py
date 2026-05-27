from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .auth import auth_status
from .config import CmsMcpConfig
from .errors import CmsMcpError
from .tools.ads_txt import (
    cms_check_ads_file_status,
    cms_get_ads_file,
    cms_get_ads_file_history,
    cms_get_ads_file_url,
    cms_list_ads_files,
)
from .tools.dimensions import cms_dimensions
from .tools.exports import (
    cms_export_period_csv,
    cms_export_sales_csv,
    cms_export_units_csv,
)
from .tools.health import cms_me
from .tools.inventories import (
    cms_get_inventory,
    cms_get_inventory_history,
    cms_list_inventories,
    cms_list_inventory_units,
)
from .tools.mediation import (
    cms_inventory_groups,
    cms_mediation_requests,
    cms_mediation_settings,
    cms_sdk_init_configs,
)
from .tools.reports import (
    cms_report_adnetwork_ssp,
    cms_report_adnetwork_unit,
    cms_report_adnetworks,
    cms_report_columns,
    cms_report_kpi,
    cms_report_media_unit,
    cms_report_metadata,
    cms_report_period,
    cms_report_sales,
)
from .tools.units import (
    cms_get_unit,
    cms_get_unit_history,
    cms_list_ssps,
    cms_list_units,
    cms_list_units_by_supplier,
    cms_search_units,
)
from .tools.users import cms_get_user_default_settings, cms_list_users


async def run_smoke(
    config: CmsMcpConfig,
    *,
    target: str = "health",
    inventory_id: str | None = None,
    ads_file_id: str | None = None,
) -> dict[str, Any]:
    target = (target or "health").strip().lower()
    result: dict[str, Any] = {
        "ok": False,
        "env": config.env,
        "target": target,
        "checks": {},
    }

    auth = await auth_status(config)
    result["checks"]["auth"] = auth
    if not auth.get("ok"):
        result["remediation"] = f"Run `cms-mcp auth login --env {config.env}`"
        return result

    if target in {"health", "basic"}:
        result["checks"]["me"] = await cms_me(config)
    elif target in {"catalog", "all"}:
        result["checks"]["me"] = await _summarized("cms_me", cms_me(config))

    if target in {"dimensions", "basic"}:
        result["checks"]["dimensions"] = await cms_dimensions(
            config,
            target="projects,os,platforms,ssps",
        )
    elif target in {"catalog", "all"}:
        result["checks"]["dimensions"] = await _summarized(
            "cms_dimensions",
            cms_dimensions(config, target="all"),
        )

    if target in {"catalog", "all"}:
        result["checks"].update(
            await _catalog_checks(
                config,
                inventory_id=inventory_id,
                ads_file_id=ads_file_id,
                include_tentative=target == "all",
            )
        )

    result["ok"] = all(
        isinstance(check, dict) and check.get("ok") for check in result["checks"].values()
    )
    return result


async def _catalog_checks(
    config: CmsMcpConfig,
    *,
    inventory_id: str | None,
    ads_file_id: str | None,
    include_tentative: bool = False,
) -> dict[str, Any]:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    checks: dict[str, Any] = {}
    selected: dict[str, Any] = {}

    checks["list_ssps"] = await _summarized("cms_list_ssps", cms_list_ssps(config))
    checks["list_users"] = await _summarized(
        "cms_list_users",
        cms_list_users(config, approval_status="APPROVED", page=1, page_size=5),
    )
    checks["user_default_settings"] = await _summarized(
        "cms_get_user_default_settings",
        cms_get_user_default_settings(config),
    )
    checks["report_metadata"] = await _summarized(
        "cms_report_metadata",
        cms_report_metadata(config, business_category_id="7"),
    )
    inventories_result, checks["list_inventories"] = await _captured(
        "cms_list_inventories",
        cms_list_inventories(config, page=1, page_size=20),
    )
    if not inventory_id:
        inventory_id = _first_inventory_id(inventories_result)
        selected["inventory_id"] = inventory_id

    units_result, checks["search_units"] = await _captured(
        "cms_search_units",
        cms_search_units(config, page=1, page_size=1),
    )
    unit_id = _first_unit_id(units_result)
    selected["unit_id"] = unit_id
    checks["list_units"] = await _summarized(
        "cms_list_units",
        cms_list_units(config, page=1, page_size=1),
    )

    checks["report_columns"] = await _summarized(
        "cms_report_columns",
        cms_report_columns(config),
    )
    checks["report_sales"] = await _summarized(
        "cms_report_sales",
        cms_report_sales(
            config,
            start_date=yesterday,
            end_date=yesterday,
            business_category_id="7",
            publisher_id="1",
            os="ALL",
            position_id="all",
        ),
    )
    checks["export_sales_csv"] = await _summarized(
        "cms_export_sales_csv",
        cms_export_sales_csv(
            config,
            start_date=yesterday,
            end_date=yesterday,
            business_category_id="7",
            publisher_id="1",
            os="ALL",
            position_id="all",
            max_rows=2,
        ),
    )
    checks["report_period"] = await _summarized(
        "cms_report_period",
        cms_report_period(
            config,
            start_date=week_ago,
            end_date=yesterday,
            business_category_id="7",
            publisher_id="1",
            os="ALL",
            position_id="all",
        ),
    )
    checks["export_period_csv"] = await _summarized(
        "cms_export_period_csv",
        cms_export_period_csv(
            config,
            start_date=week_ago,
            end_date=yesterday,
            business_category_id="7",
            publisher_id="1",
            os="ALL",
            position_id="all",
            max_rows=2,
        ),
    )
    checks["report_kpi"] = await _summarized(
        "cms_report_kpi",
        cms_report_kpi(
            config,
            start_date=week_ago,
            end_date=yesterday,
            business_category_id="7",
            publisher_id="1",
            os="ALL",
            position_id="all",
        ),
    )
    adnetworks_result, checks["report_adnetworks"] = await _captured(
        "cms_report_adnetworks",
        cms_report_adnetworks(
            config,
            date=yesterday,
            business_category_id="7",
            publisher_id="1",
            os="ALL",
            position_id="all",
        ),
    )
    ssp_id = _first_id(adnetworks_result)
    selected["ssp_id"] = ssp_id
    ads_files_result, checks["list_ads_files"] = await _captured(
        "cms_list_ads_files",
        cms_list_ads_files(config, platform="APP"),
    )
    if not ads_file_id:
        ads_file_id = _first_id(ads_files_result)
        selected["ads_file_id"] = ads_file_id

    checks["sdk_init_configs"] = await _summarized(
        "cms_sdk_init_configs",
        cms_sdk_init_configs(config, project="CASHWALK", os="ANDROID"),
    )

    if include_tentative and ssp_id:
        checks["report_adnetwork_ssp"] = await _summarized(
            "cms_report_adnetwork_ssp",
            cms_report_adnetwork_ssp(
                config,
                ssp_id=ssp_id,
                start_date=week_ago,
                end_date=yesterday,
                business_category_id="7",
                publisher_id="1",
                os="ALL",
                position_id="all",
                page=1,
                page_size=1,
            ),
        )
        checks["report_adnetwork_unit"] = await _summarized(
            "cms_report_adnetwork_unit",
            cms_report_adnetwork_unit(
                config,
                adnetwork_unit_id=ssp_id,
                start_date=week_ago,
                end_date=yesterday,
                business_category_id="7",
                publisher_id="1",
                os="ALL",
                position_id="all",
                page=1,
                page_size=1,
            ),
        )
        checks["report_media_unit"] = await _summarized(
            "cms_report_media_unit",
            cms_report_media_unit(
                config,
                media_unit_id=ssp_id,
                start_date=week_ago,
                end_date=yesterday,
                business_category_id="7",
                publisher_id="1",
                os="ALL",
                position_id="all",
                page=1,
                page_size=1,
            ),
        )

    if include_tentative:
        checks["list_units_by_supplier"] = await _summarized(
            "cms_list_units_by_supplier",
            cms_list_units_by_supplier(
                config,
                supplier="ADMOB",
                include_rows=False,
                sample_size=1,
            ),
        )
        checks["export_units_csv"] = await _summarized(
            "cms_export_units_csv",
            cms_export_units_csv(config, page=1, page_size=2, max_rows=2),
        )

    if inventory_id:
        checks["get_inventory"] = await _summarized(
            "cms_get_inventory",
            cms_get_inventory(config, inventory_id=inventory_id),
        )
        checks["get_inventory_history"] = await _summarized(
            "cms_get_inventory_history",
            cms_get_inventory_history(config, inventory_id=inventory_id),
        )
        checks["list_inventory_units"] = await _summarized(
            "cms_list_inventory_units",
            cms_list_inventory_units(config, inventory_id=inventory_id, page=1, page_size=1),
        )
        checks["mediation_requests"] = await _summarized(
            "cms_mediation_requests",
            cms_mediation_requests(config, inventory_id=inventory_id),
        )
        if include_tentative:
            checks["mediation_settings"] = await _summarized(
                "cms_mediation_settings",
                cms_mediation_settings(config, inventory_id=inventory_id),
            )
            checks["inventory_groups"] = await _summarized(
                "cms_inventory_groups",
                cms_inventory_groups(config, inventory_id=inventory_id),
            )

    if unit_id:
        checks["get_unit"] = await _summarized(
            "cms_get_unit",
            cms_get_unit(config, unit_id=unit_id),
        )
        checks["get_unit_history"] = await _summarized(
            "cms_get_unit_history",
            cms_get_unit_history(config, unit_id=unit_id),
        )

    if ads_file_id:
        checks["get_ads_file"] = await _summarized(
            "cms_get_ads_file",
            cms_get_ads_file(config, ads_file_id=ads_file_id),
        )
        checks["check_ads_file_status"] = await _summarized(
            "cms_check_ads_file_status",
            cms_check_ads_file_status(config, ads_file_id=ads_file_id),
        )
        checks["get_ads_file_url"] = await _summarized(
            "cms_get_ads_file_url",
            cms_get_ads_file_url(config, ads_file_id=ads_file_id),
        )
        checks["get_ads_file_history"] = await _summarized(
            "cms_get_ads_file_history",
            cms_get_ads_file_history(config, ads_file_id=ads_file_id),
        )

    checks["selected_ids"] = {
        "ok": True,
        "tool": "smoke_auto_select",
        "data": selected,
    }
    return checks


async def _captured(name: str, awaitable: Any) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        result = await awaitable
    except CmsMcpError as exc:
        return None, {
            "ok": False,
            "tool": name,
            "error": exc.to_tool_result()["error"],
        }
    except Exception as exc:  # noqa: BLE001 - live smoke boundary
        return None, {
            "ok": False,
            "tool": name,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": type(exc).__name__,
            },
        }
    return result, _summarize_result(name, result)


async def _summarized(name: str, awaitable: Any) -> dict[str, Any]:
    try:
        result = await awaitable
    except CmsMcpError as exc:
        return {
            "ok": False,
            "tool": name,
            "error": exc.to_tool_result()["error"],
        }
    except Exception as exc:  # noqa: BLE001 - live smoke boundary
        return {
            "ok": False,
            "tool": name,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": type(exc).__name__,
            },
        }

    return _summarize_result(name, result)


def _summarize_result(name: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "tool": name,
        "path": result.get("path"),
        "schema_status": result.get("schema_status"),
        "shape": _shape(result.get("data")),
        "warnings": result.get("warnings", []),
    }


def _shape(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        return {
            "type": "list",
            "length": len(value),
            "first_item_keys": sorted(value[0].keys()) if value and isinstance(value[0], dict) else None,
        }
    if isinstance(value, dict):
        rows = _find_rows(value)
        return {
            "type": "dict",
            "keys": sorted(value.keys()),
            "row_count": len(rows) if rows is not None else None,
            "row_keys": sorted(rows[0].keys()) if rows and isinstance(rows[0], dict) else None,
        }
    return {"type": type(value).__name__}


def _find_rows(value: dict[str, Any]) -> list[Any] | None:
    for key in ("data", "items", "rows", "content", "result"):
        candidate = value.get(key)
        if isinstance(candidate, list):
            return candidate
    return None


def _first_id(result: dict[str, Any] | None) -> str | None:
    if not result:
        return None
    data = result.get("data")
    rows: list[Any] | None
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = _find_rows(data)
    else:
        rows = None
    if not rows:
        return None
    first = rows[0]
    if not isinstance(first, dict):
        return None
    for key in ("id", "inventoryId", "adsFileId"):
        value = first.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _first_inventory_id(result: dict[str, Any] | None) -> str | None:
    rows = _rows_from_result(result)
    if not rows:
        return None
    preferred = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("mediationStatus") is True
    ]
    candidates = preferred or rows
    first = candidates[0]
    if not isinstance(first, dict):
        return None
    value = first.get("id") or first.get("inventoryId")
    return str(value) if value not in (None, "") else None


def _first_unit_id(result: dict[str, Any] | None) -> str | None:
    rows = _rows_from_result(result)
    if not rows:
        return None
    first = rows[0]
    if not isinstance(first, dict):
        return None
    candidates = [first, first.get("unit")]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for key in ("id", "unitId", "unit_id", "nudgeUnitId"):
            value = candidate.get(key)
            if value not in (None, ""):
                return str(value)
    return None


def _rows_from_result(result: dict[str, Any] | None) -> list[Any] | None:
    if not result:
        return None
    data = result.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return _find_rows(data)
    return None
