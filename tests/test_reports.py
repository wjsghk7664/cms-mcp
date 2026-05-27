from __future__ import annotations

import pytest

from cms_mcp.errors import CmsMcpError, ErrorCode
from cms_mcp.tools.reports import _default_range


def test_default_range_uses_end_date_when_start_date_is_missing() -> None:
    assert _default_range(start_date=None, end_date="2026-05-27", days=7) == (
        "2026-05-21",
        "2026-05-27",
    )


def test_default_range_rejects_invalid_dates() -> None:
    with pytest.raises(CmsMcpError) as exc:
        _default_range(start_date=None, end_date="2026/05/27")

    assert exc.value.code == ErrorCode.VALIDATION_ERROR
