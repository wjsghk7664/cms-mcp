from __future__ import annotations

import stat
from pathlib import Path

from cms_mcp.config import CmsMcpConfig
from cms_mcp.cookie_store import CookieStore


def make_config(tmp_path: Path) -> CmsMcpConfig:
    return CmsMcpConfig(
        env="prod",
        api_base="https://ad-manager-api.cashwalk.io",
        cms_frontend="https://ad-cms.cashwalk.io",
        cookie_file=tmp_path / ".cms-mcp" / "cookies" / "prod.json",
        auth_profile_dir=tmp_path / ".cms-mcp" / "browser-profile" / "prod",
    )


def test_cookie_store_save_sets_owner_only_permissions(tmp_path: Path) -> None:
    store = CookieStore(make_config(tmp_path))
    store.save(
        [
            {
                "name": "session",
                "value": "secret-value",
                "domain": "ad-manager-api.cashwalk.io",
                "path": "/",
            }
        ]
    )

    assert store.path.exists()
    mode = stat.S_IMODE(store.path.stat().st_mode)
    assert mode == 0o600


def test_cookie_store_status_missing(tmp_path: Path) -> None:
    store = CookieStore(make_config(tmp_path))
    status = store.status()

    assert status.state == "MISSING"
    assert not status.exists


def test_sanitized_payload_redacts_cookie_values(tmp_path: Path) -> None:
    store = CookieStore(make_config(tmp_path))
    store.save(
        [
            {
                "name": "session",
                "value": "secret-value",
                "domain": "ad-manager-api.cashwalk.io",
                "path": "/",
            }
        ]
    )

    payload = store.sanitized_payload()
    assert payload["cookies"] == "[REDACTED]"


def test_delete_only_removes_project_auth_state(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    store = CookieStore(config)
    store.save(
        [
            {
                "name": "session",
                "value": "secret-value",
                "domain": "ad-manager-api.cashwalk.io",
                "path": "/",
            }
        ]
    )
    config.auth_profile_dir.mkdir(parents=True)
    (config.auth_profile_dir / "profile-file").write_text("local", encoding="utf-8")

    result = store.delete(include_browser_profile=True)

    assert not config.cookie_file.exists()
    assert not config.auth_profile_dir.exists()
    assert str(config.cookie_file) in result["removed"]

