from __future__ import annotations

from cms_mcp.tools.inventories import normalize_app_name


def test_normalize_app_name_maps_korean_cashwalk_alias() -> None:
    assert normalize_app_name("한국캐시워크") == "캐시워크"


def test_normalize_app_name_preserves_cms_app_label() -> None:
    assert normalize_app_name(" 캐시워크 ") == "캐시워크"
