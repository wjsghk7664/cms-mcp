from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from .config import CmsMcpConfig
from .cookie_store import CookieStore
from .endpoints import assert_readonly, normalize_path
from .errors import CmsMcpError, ErrorCode
from .utils.redaction import redact


class CmsClient:
    def __init__(
        self,
        config: CmsMcpConfig,
        *,
        cookie_store: CookieStore | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        auto_auth: bool | None = None,
    ) -> None:
        self.config = config
        self.cookie_store = cookie_store or CookieStore(config)
        self.transport = transport
        self.auto_auth = (
            config.auto_login if auto_auth is None and transport is None else bool(auto_auth)
        )

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        schema_status: str = "confirmed",
    ) -> dict[str, Any]:
        assert_readonly(method, path, self.config.allow_post_reads)
        normalized_method = method.upper()
        normalized_path = normalize_path(path)
        if self.auto_auth:
            from .auth_guard import ensure_authenticated

            await ensure_authenticated(self.config)
        cookies = self.cookie_store.load_cookies()
        url = urljoin(self.config.api_base + "/", normalized_path.lstrip("/"))

        try:
            async with httpx.AsyncClient(
                cookies=cookies,
                timeout=self.config.timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as http:
                response = await http.request(
                    normalized_method,
                    url,
                    params=query,
                    json=body,
                    headers={"Accept": "application/json"},
                )
        except httpx.TimeoutException as exc:
            raise CmsMcpError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message="CMS API request timed out",
                details={"path": normalized_path},
            ) from exc
        except httpx.HTTPError as exc:
            raise CmsMcpError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message="CMS API request failed",
                details={"path": normalized_path, "error": str(exc)},
            ) from exc

        if response.status_code in {401, 403}:
            raise CmsMcpError(
                code=ErrorCode.AUTH_REQUIRED
                if response.status_code == 401
                else ErrorCode.UPSTREAM_FORBIDDEN,
                message="CMS session is missing, expired, or not authorized",
                status_code=response.status_code,
                details={
                    "path": normalized_path,
                    "remediation": f"Run `cms-mcp auth login --env {self.config.env}`",
                },
            )
        if response.status_code == 404:
            raise CmsMcpError(
                code=ErrorCode.UPSTREAM_NOT_FOUND,
                message="CMS API endpoint or resource was not found",
                status_code=response.status_code,
                details={"path": normalized_path},
            )
        if response.status_code == 429:
            raise CmsMcpError(
                code=ErrorCode.RATE_LIMITED,
                message="CMS API rate limit reached",
                status_code=response.status_code,
                details={"path": normalized_path},
            )
        if response.status_code >= 400:
            raise CmsMcpError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message="CMS API returned an error",
                status_code=response.status_code,
                details={
                    "path": normalized_path,
                    "body": redact(response.text[:500]),
                },
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise CmsMcpError(
                code=ErrorCode.SCHEMA_UNCONFIRMED,
                message="CMS API did not return JSON",
                status_code=response.status_code,
                details={"path": normalized_path},
            ) from exc

        result = {
            "ok": True,
            "env": self.config.env,
            "source": "cms_api",
            "api_base": self.config.api_base,
            "path": normalized_path,
            "schema_status": schema_status,
            "data": redact(data),
        }
        return result

    async def get(
        self,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        schema_status: str = "confirmed",
    ) -> dict[str, Any]:
        return await self.request_json(
            "GET",
            path,
            query=query,
            schema_status=schema_status,
        )

    async def post_read(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        schema_status: str = "confirmed",
    ) -> dict[str, Any]:
        return await self.request_json(
            "POST",
            path,
            query=query,
            body=body,
            schema_status=schema_status,
        )

    async def probe(self) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []
        for path in ("/users/me", "/inventories/projects"):
            try:
                result = await self.get(path)
                return {
                    "ok": True,
                    "env": self.config.env,
                    "source": "cms_api",
                    "probe_path": path,
                    "cookie_file": str(self.config.cookie_file),
                    "data": result["data"],
                }
            except CmsMcpError as exc:
                errors.append(exc.to_tool_result()["error"])
        raise CmsMcpError(
            code=ErrorCode.AUTH_REQUIRED,
            message="CMS auth probe failed. Run auth login and try again.",
            details={
                "env": self.config.env,
                "cookie_file": str(self.config.cookie_file),
                "remediation": f"Run `cms-mcp auth login --env {self.config.env}`",
                "probe_errors": errors,
            },
        )
