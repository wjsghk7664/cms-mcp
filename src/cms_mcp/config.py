from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .errors import CmsMcpError, ErrorCode

CmsEnv = Literal["prod", "test"]

CMS_FRONTENDS: dict[CmsEnv, str] = {
    "prod": "https://ad-cms.cashwalk.io",
    "test": "https://test-ad-cms.cashwalk.io",
}

API_BASES: dict[CmsEnv, str] = {
    "prod": "https://ad-manager-api.cashwalk.io",
    "test": "https://test-ad-manager-api.cashwalk.io",
}


@dataclass(frozen=True, slots=True)
class CmsMcpConfig:
    env: CmsEnv
    api_base: str
    cms_frontend: str
    cookie_file: Path
    auth_profile_dir: Path
    timeout_seconds: float = 30.0
    allow_post_reads: bool = True
    log_level: str = "INFO"


def normalize_env(raw_env: str | None) -> CmsEnv:
    env = (raw_env or "prod").strip().lower()
    if env not in ("prod", "test"):
        raise CmsMcpError(
            code=ErrorCode.VALIDATION_ERROR,
            message="CMS env must be one of: prod, test",
            details={"env": env},
        )
    return env  # type: ignore[return-value]


def load_config(env: str | None = None) -> CmsMcpConfig:
    resolved_env = normalize_env(env or os.environ.get("CMS_MCP_ENV"))
    root = Path.cwd()
    api_base = os.environ.get("CMS_MCP_API_BASE") or API_BASES[resolved_env]
    cms_frontend = CMS_FRONTENDS[resolved_env]
    cookie_file = Path(
        os.environ.get("CMS_MCP_COOKIE_FILE")
        or root / ".cms-mcp" / "cookies" / f"{resolved_env}.json"
    )
    auth_profile_dir = Path(
        os.environ.get("CMS_MCP_AUTH_PROFILE_DIR")
        or root / ".cms-mcp" / "browser-profile" / resolved_env
    )

    return CmsMcpConfig(
        env=resolved_env,
        api_base=api_base.rstrip("/"),
        cms_frontend=cms_frontend.rstrip("/"),
        cookie_file=cookie_file,
        auth_profile_dir=auth_profile_dir,
        timeout_seconds=float(os.environ.get("CMS_MCP_TIMEOUT_SECONDS", "30")),
        allow_post_reads=os.environ.get("CMS_MCP_ALLOW_POST_READS", "true").lower()
        not in {"0", "false", "no"},
        log_level=os.environ.get("CMS_MCP_LOG_LEVEL", "INFO"),
    )
