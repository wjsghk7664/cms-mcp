from __future__ import annotations

from cms_mcp.tools.dimensions import _resolve_targets


def test_all_dimensions_include_confirmed_currency_but_not_apps() -> None:
    targets = _resolve_targets("all")

    assert "currencies" in targets
    assert "apps" not in targets
