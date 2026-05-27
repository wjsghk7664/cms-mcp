from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .errors import CmsMcpError, ErrorCode

READ_ONLY_POST_PATHS = {
    "/units/search",
}

BLOCKED_PATH_PATTERNS = (
    re.compile(r"^/auth/logout/?$"),
    re.compile(r"^/ads-files/[^/]+/callback/?$"),
)


@dataclass(frozen=True, slots=True)
class Endpoint:
    method: str
    path: str
    schema_status: str = "confirmed"


def normalize_path(path: str) -> str:
    if not path:
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Endpoint path is required",
        )
    if path.startswith("http://") or path.startswith("https://"):
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Only relative API paths are allowed",
        )
    normalized = "/" + path.lstrip("/")
    return normalized.split("?", 1)[0]


def assert_readonly(method: str, path: str, allow_post_reads: bool = True) -> None:
    normalized_method = method.upper()
    normalized_path = normalize_path(path)

    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern.match(normalized_path):
            raise CmsMcpError(
                code=ErrorCode.FORBIDDEN_READONLY,
                message="Endpoint is blocked by the read-only guard",
                details={"method": normalized_method, "path": normalized_path},
            )

    if normalized_method == "GET":
        return

    if (
        normalized_method == "POST"
        and allow_post_reads
        and normalized_path in READ_ONLY_POST_PATHS
    ):
        return

    raise CmsMcpError(
        code=ErrorCode.FORBIDDEN_READONLY,
        message="HTTP method is not allowed in read-only mode",
        details={"method": normalized_method, "path": normalized_path},
    )


def build_path(template: str, **params: object) -> str:
    path = template
    for key, value in params.items():
        if value is None or value == "":
            raise CmsMcpError(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"Missing required path parameter: {key}",
            )
        path = path.replace("{" + key + "}", str(value))
    if "{" in path or "}" in path:
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Unresolved path template parameter",
            details={"path": path},
        )
    return path


def compact_query(query: dict[str, object | None]) -> dict[str, object]:
    return {key: value for key, value in query.items() if value not in (None, "")}


def comma_join(values: Iterable[str] | None) -> str | None:
    if values is None:
        return None
    filtered = [value for value in values if value]
    return ",".join(filtered) if filtered else None

