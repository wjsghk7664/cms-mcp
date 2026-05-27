from __future__ import annotations

import pytest

from cms_mcp.endpoints import assert_readonly
from cms_mcp.errors import CmsMcpError, ErrorCode


def test_get_is_allowed() -> None:
    assert_readonly("GET", "/inventories")


def test_units_search_post_is_allowed() -> None:
    assert_readonly("POST", "/units/search")


@pytest.mark.parametrize("method", ["PATCH", "PUT", "DELETE"])
def test_mutation_methods_are_blocked(method: str) -> None:
    with pytest.raises(CmsMcpError) as exc:
        assert_readonly(method, "/inventories/1")
    assert exc.value.code == ErrorCode.FORBIDDEN_READONLY


def test_non_whitelisted_post_is_blocked() -> None:
    with pytest.raises(CmsMcpError):
        assert_readonly("POST", "/inventories")


@pytest.mark.parametrize(
    "path",
    [
        "/auth/logout",
        "/ads-files/123/callback",
    ],
)
def test_risky_action_paths_are_blocked(path: str) -> None:
    with pytest.raises(CmsMcpError) as exc:
        assert_readonly("GET", path)
    assert exc.value.code == ErrorCode.FORBIDDEN_READONLY


def test_absolute_urls_are_rejected() -> None:
    with pytest.raises(CmsMcpError):
        assert_readonly("GET", "https://example.com/inventories")

