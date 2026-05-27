from __future__ import annotations

from typing import Any

import httpx

from .client import CmsClient
from .config import CmsMcpConfig
from .cookie_store import CookieStore
from .errors import CmsMcpError


async def auth_status(
    config: CmsMcpConfig,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    store = CookieStore(config)
    local_status = store.status().to_dict()
    result: dict[str, Any] = {
        "ok": False,
        "env": config.env,
        "api_base": config.api_base,
        "cookie_file": str(config.cookie_file),
        "local": local_status,
    }
    if local_status["state"] != "PRESENT":
        result["state"] = local_status["state"]
        result["remediation"] = f"Run `cms-mcp auth login --env {config.env}`"
        return result

    client = CmsClient(config, cookie_store=store, transport=transport)
    try:
        probe = await client.probe()
    except CmsMcpError as exc:
        result["state"] = "REJECTED"
        result["error"] = exc.to_tool_result()["error"]
        result["remediation"] = f"Run `cms-mcp auth login --env {config.env}`"
        return result

    result["ok"] = True
    result["state"] = "OK"
    result["probe"] = {
        "path": probe["probe_path"],
        "source": probe["source"],
    }
    return result

