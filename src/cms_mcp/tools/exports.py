from __future__ import annotations

import csv
from datetime import date, timedelta
from io import StringIO
from typing import Any

from cms_mcp.config import CmsMcpConfig
from cms_mcp.tools.reports import cms_report_kpi, cms_report_sales
from cms_mcp.tools.units import cms_search_units

PLATFORM_LABELS = {
    "ANDROID": "AOS",
    "IOS": "IOS",
    "WEB": "WEB",
}


async def cms_export_sales_csv(
    config: CmsMcpConfig,
    *,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    filename: str | None = None,
    max_rows: int = 5000,
) -> dict[str, Any]:
    result = await cms_report_sales(
        config,
        start_date=start_date,
        end_date=end_date,
        business_category_id=business_category_id,
        publisher_id=publisher_id,
        os=os,
        position_id=position_id,
    )
    rows = _limit_rows(_sales_rows(result.get("data")), max_rows)
    return _csv_result(
        config,
        filename=filename or _filename("cms-sales", start_date, end_date),
        rows=rows.rows,
        schema_status="client_side_csv_confirmed_frontend",
        warnings=rows.warnings,
    )


async def cms_export_period_csv(
    config: CmsMcpConfig,
    *,
    start_date: str = "",
    end_date: str = "",
    business_category_id: str | None = None,
    publisher_id: str | None = None,
    os: str | None = None,
    position_id: str | None = None,
    filename: str | None = None,
    max_rows: int = 5000,
) -> dict[str, Any]:
    result = await cms_report_kpi(
        config,
        start_date=start_date,
        end_date=end_date,
        business_category_id=business_category_id,
        publisher_id=publisher_id,
        os=os,
        position_id=position_id,
    )
    data = result.get("data")
    rows = _limit_rows(data.get("data") if isinstance(data, dict) else [], max_rows)
    return _csv_result(
        config,
        filename=filename or _filename("cms-period", start_date, end_date),
        rows=rows.rows,
        schema_status="client_side_csv_confirmed_frontend",
        warnings=rows.warnings,
    )


async def cms_export_units_csv(
    config: CmsMcpConfig,
    *,
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
    result = await cms_search_units(
        config,
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
    data = result.get("data")
    rows = _limit_rows(_unit_rows(data.get("data") if isinstance(data, dict) else []), max_rows)
    warnings = rows.warnings
    if isinstance(data, dict) and data.get("total", 0) and len(rows.rows) < data["total"]:
        warnings.append(
            "CSV includes the current requested page only. Increase page_size or page through results for more rows."
        )
    return _csv_result(
        config,
        filename=filename or "cms-units.csv",
        rows=rows.rows,
        schema_status="client_side_csv_confirmed_frontend",
        warnings=warnings,
    )


class LimitedRows:
    def __init__(self, rows: list[dict[str, Any]], warnings: list[str]) -> None:
        self.rows = rows
        self.warnings = warnings


def _sales_rows(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    by_platform = data.get("dataByPlatform")
    if not isinstance(by_platform, dict):
        return []

    rows_by_date: dict[str, dict[str, Any]] = {}
    for platform, entries in by_platform.items():
        if not isinstance(entries, list):
            continue
        platform_label = PLATFORM_LABELS.get(str(platform), str(platform))
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            row = rows_by_date.setdefault(
                str(entry.get("date") or ""),
                {
                    "date": entry.get("date"),
                    "total": 0,
                    "status": "Original",
                },
            )
            row["total"] = _number(row.get("total")) + _number(entry.get("total"))
            if entry.get("status") == "Estimated":
                row["status"] = "Estimated"
            positions = entry.get("positions")
            if not isinstance(positions, list):
                continue
            for position in positions:
                if not isinstance(position, dict):
                    continue
                label = position.get("label")
                if not label:
                    continue
                key = f"{platform_label}_{label}"
                row[key] = _number(row.get(key)) + _number(position.get("total"))

    return sorted(rows_by_date.values(), key=lambda row: str(row.get("date")), reverse=True)


def _unit_rows(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        unit = item.get("unit") if isinstance(item.get("unit"), dict) else {}
        inventory = item.get("inventory") if isinstance(item.get("inventory"), dict) else {}
        project = inventory.get("project") if isinstance(inventory.get("project"), dict) else {}
        publisher = inventory.get("publisher") if isinstance(inventory.get("publisher"), dict) else {}
        tenant = inventory.get("tenant") if isinstance(inventory.get("tenant"), dict) else {}
        rows.append(
            {
                "inventory_id": inventory.get("inventoryId") or unit.get("inventoryId"),
                "project_code": project.get("code"),
                "project_name": project.get("name"),
                "publisher_code": publisher.get("code"),
                "publisher_name": publisher.get("nameKr") or publisher.get("name"),
                "platform": inventory.get("platform"),
                "app_platform": inventory.get("appPlatform"),
                "screen": inventory.get("screenName") or inventory.get("screen"),
                "location": inventory.get("locationName") or inventory.get("location"),
                "tenant": (tenant.get("name") or tenant.get("code")) if tenant else None,
                "position_id": inventory.get("positionId"),
                "unit_id": unit.get("unitId") or unit.get("id"),
                "unit_label": unit.get("label"),
                "supplier": unit.get("supplier"),
                "supplier_unit_id": unit.get("supplierUnitId"),
                "supplier_sub_id": unit.get("supplierSubId"),
                "format": unit.get("format"),
                "size": unit.get("size"),
                "timeout": unit.get("timeout"),
                "purpose": unit.get("purpose"),
                "preload": unit.get("preload"),
                "visibility": unit.get("visibility"),
                "is_reporting": unit.get("isReporting"),
                "mediation_status": unit.get("mediationStatus"),
                "updated_at": unit.get("updatedAt"),
            }
        )
    return rows


def _limit_rows(rows: Any, max_rows: int) -> LimitedRows:
    normalized = rows if isinstance(rows, list) else []
    if max_rows <= 0:
        return LimitedRows([], ["max_rows <= 0, so no rows were included."])
    if len(normalized) <= max_rows:
        return LimitedRows(normalized, [])
    return LimitedRows(
        normalized[:max_rows],
        [f"CSV was truncated from {len(normalized)} rows to max_rows={max_rows}."],
    )


def _csv_result(
    config: CmsMcpConfig,
    *,
    filename: str,
    rows: list[dict[str, Any]],
    schema_status: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "ok": True,
        "env": config.env,
        "source": "cms_api_client_side_csv",
        "schema_status": schema_status,
        "data": {
            "filename": filename if filename.endswith(".csv") else f"{filename}.csv",
            "content_type": "text/csv; charset=utf-8",
            "row_count": len(rows),
            "csv": _rows_to_csv(rows),
        },
        "warnings": warnings,
    }


def _rows_to_csv(rows: list[dict[str, Any]]) -> str:
    output = StringIO()
    fieldnames = _fieldnames(rows)
    if not fieldnames:
        return ""
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames


def _number(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _filename(prefix: str, start_date: str, end_date: str) -> str:
    if start_date and end_date:
        return f"{prefix}-{start_date}-{end_date}.csv"
    if end_date:
        return f"{prefix}-{end_date}.csv"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    return f"{prefix}-{yesterday}.csv"
