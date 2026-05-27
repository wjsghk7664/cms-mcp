from __future__ import annotations

from pathlib import Path

import pytest

from cms_mcp.config import CmsMcpConfig
from cms_mcp.smoke import run_smoke


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


@pytest.mark.asyncio
async def test_smoke_reports_missing_auth(tmp_path: Path) -> None:
    result = await run_smoke(make_config(tmp_path), target="basic")

    assert result["ok"] is False
    assert result["checks"]["auth"]["state"] == "MISSING"
    assert "auth login" in result["remediation"]

