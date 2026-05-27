from __future__ import annotations

from pathlib import Path

import pytest

from cms_mcp.config import load_config, normalize_env
from cms_mcp.errors import CmsMcpError


def test_normalize_env_defaults_to_prod() -> None:
    assert normalize_env(None) == "prod"


def test_normalize_env_rejects_unknown() -> None:
    with pytest.raises(CmsMcpError):
        normalize_env("stage")


def test_load_config_uses_project_cookie_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CMS_MCP_COOKIE_FILE", raising=False)
    monkeypatch.delenv("CMS_MCP_AUTO_LOGIN", raising=False)
    config = load_config("test")

    assert config.env == "test"
    assert config.api_base == "https://test-ad-manager-api.cashwalk.io"
    assert config.cookie_file == tmp_path / ".cms-mcp" / "cookies" / "test.json"
    assert config.auto_login is True


def test_load_config_uses_auto_login_env_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CMS_MCP_AUTO_LOGIN", "false")
    monkeypatch.setenv("CMS_MCP_AUTO_LOGIN_TIMEOUT_SECONDS", "10")
    monkeypatch.setenv("CMS_MCP_AUTO_LOGIN_HEADLESS", "true")

    config = load_config("prod")

    assert config.auto_login is False
    assert config.auto_login_timeout_seconds == 10
    assert config.auto_login_headless is True
