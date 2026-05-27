from __future__ import annotations

from pathlib import Path

import pytest

from cms_mcp.server import mcp


@pytest.mark.asyncio
async def test_server_registers_readonly_tools() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}

    assert "cms_health" in names
    assert "cms_dimensions" in names
    assert "cms_list_users" in names
    assert "cms_get_user_default_settings" in names
    assert "cms_list_units" in names
    assert "cms_list_units_by_supplier" in names
    assert "cms_export_units_csv" in names
    assert "cms_search_units" in names
    assert "cms_get_unit" in names
    assert "cms_list_inventories" in names
    assert "cms_check_ads_file_status" in names
    assert "cms_report_adnetwork_ssp" in names
    assert "cms_report_adnetwork_unit" in names
    assert "cms_report_media_unit" in names
    assert "cms_report_period" in names
    assert "cms_export_period_csv" in names
    assert "cms_report_kpi" in names
    assert "cms_export_sales_csv" in names
    assert "cms_report_metadata" in names
    assert "cms_get_ads_file_url" in names
    assert "cms_inventory_groups" in names
    assert "cms_mediation_settings" in names
    assert "cms_sdk_init_configs" in names
    assert "cms_mediation_requests" in names
    assert len(names) == 37


@pytest.mark.asyncio
async def test_health_tool_handles_missing_cookie(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CMS_MCP_COOKIE_FILE", str(tmp_path / "missing.json"))
    _content, structured = await mcp.call_tool("cms_health", {"env": "prod"})

    assert structured["ok"] is False
    assert structured["state"] in {"MISSING", "REJECTED"}
