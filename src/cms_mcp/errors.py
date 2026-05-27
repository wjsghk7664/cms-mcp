from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ErrorCode:
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_STALE = "AUTH_STALE"
    FORBIDDEN_READONLY = "FORBIDDEN_READONLY"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UPSTREAM_FORBIDDEN = "UPSTREAM_FORBIDDEN"
    UPSTREAM_NOT_FOUND = "UPSTREAM_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SCHEMA_UNCONFIRMED = "SCHEMA_UNCONFIRMED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(slots=True)
class CmsMcpError(Exception):
    code: str
    message: str
    status_code: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_tool_result(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }
        if self.status_code is not None:
            result["error"]["status_code"] = self.status_code
        if self.details:
            result["error"]["details"] = self.details
        return result


def error_result(error: Exception) -> dict[str, Any]:
    if isinstance(error, CmsMcpError):
        return error.to_tool_result()
    return CmsMcpError(
        code=ErrorCode.INTERNAL_ERROR,
        message="Unexpected internal error",
    ).to_tool_result()

