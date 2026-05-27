from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from cms_mcp.errors import CmsMcpError, error_result

T = TypeVar("T")


async def tool_result(call: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    try:
        return await call()
    except CmsMcpError as exc:
        return exc.to_tool_result()
    except Exception as exc:  # noqa: BLE001 - MCP tool boundary
        return error_result(exc)


def compact_result(
    result: dict[str, Any],
    *,
    limit: int | None = None,
    include_rows: bool = True,
) -> dict[str, Any]:
    if include_rows or limit is None:
        return result
    data = result.get("data")
    rows = _extract_rows(data)
    if rows is None:
        return result
    compact = dict(result)
    compact["data"] = {
        "row_count": len(rows),
        "sample": rows[:limit],
    }
    compact["warnings"] = [
        f"Rows omitted. Re-run with include_rows=true or increase limit to inspect more than {limit} rows."
    ]
    return compact


def _extract_rows(data: Any) -> list[Any] | None:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "items", "rows", "content", "result"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return None

