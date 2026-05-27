from __future__ import annotations

from typing import Any

from cms_mcp.client import CmsClient
from cms_mcp.config import CmsMcpConfig
from cms_mcp.errors import CmsMcpError, ErrorCode

DIMENSION_ENDPOINTS = {
    "os": "/inventories/os",
    "platforms": "/inventories/platforms",
    "projects": "/inventories/projects",
    "apps": "/inventories/apps",
    "publishers": "/inventories/publishers",
    "screens": "/inventories/screens",
    "locations": "/inventories/locations",
    "tenants": "/inventories/tenants",
    "ssps": "/units/ssps",
    "formats": "/units/formats",
    "sizes": "/units/sizes",
    "countries": "/units/countries",
    "currencies": "/units/legacy/currency",
}

CONFIRMED_DIMENSION_TARGETS = [
    "os",
    "platforms",
    "projects",
    "publishers",
    "screens",
    "locations",
    "tenants",
    "ssps",
    "formats",
    "sizes",
    "countries",
    "currencies",
]


async def cms_dimensions(config: CmsMcpConfig, target: str = "all") -> dict[str, Any]:
    targets = _resolve_targets(target)
    client = CmsClient(config)
    data: dict[str, Any] = {}
    errors: dict[str, Any] = {}
    for name in targets:
        try:
            data[name] = (await client.get(DIMENSION_ENDPOINTS[name]))["data"]
        except CmsMcpError as exc:
            errors[name] = exc.to_tool_result()["error"]
    return {
        "ok": not errors,
        "env": config.env,
        "source": "cms_api",
        "schema_status": "confirmed_bundle",
        "data": data,
        "errors": errors,
    }


def _resolve_targets(target: str) -> list[str]:
    normalized = (target or "all").strip().lower()
    if normalized == "all":
        return CONFIRMED_DIMENSION_TARGETS
    requested = [part.strip() for part in normalized.split(",") if part.strip()]
    unknown = [part for part in requested if part not in DIMENSION_ENDPOINTS]
    if unknown:
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Unknown dimension target",
            details={
                "unknown": unknown,
                "allowed": sorted(DIMENSION_ENDPOINTS),
            },
        )
    return requested
