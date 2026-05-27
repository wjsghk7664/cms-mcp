from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .config import CmsMcpConfig
from .errors import CmsMcpError, ErrorCode
from .utils.redaction import redact


@dataclass(frozen=True, slots=True)
class CookieStatus:
    state: str
    path: Path
    exists: bool
    age_seconds: float | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "path": str(self.path),
            "exists": self.exists,
            "age_seconds": self.age_seconds,
            "message": self.message,
        }


class CookieStore:
    def __init__(self, config: CmsMcpConfig):
        self.config = config
        self.path = config.cookie_file

    def save(self, cookies: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "env": self.config.env,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "api_base": self.config.api_base,
            "cms_frontend": self.config.cms_frontend,
            "cookies": cookies,
        }
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.chmod(tmp_path, 0o600)
        tmp_path.replace(self.path)
        os.chmod(self.path, 0o600)

    def load_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            raise CmsMcpError(
                code=ErrorCode.AUTH_REQUIRED,
                message=f"CMS cookie file is missing. Run `cms-mcp auth login --env {self.config.env}`.",
                details={"env": self.config.env, "cookie_file": str(self.path)},
            )
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CmsMcpError(
                code=ErrorCode.AUTH_STALE,
                message="CMS cookie file is malformed. Run auth login again.",
                details={"cookie_file": str(self.path)},
            ) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("cookies"), list):
            raise CmsMcpError(
                code=ErrorCode.AUTH_STALE,
                message="CMS cookie file does not match the expected format.",
                details={"cookie_file": str(self.path)},
            )
        return payload

    def load_cookies(self) -> httpx.Cookies:
        payload = self.load_payload()
        jar = httpx.Cookies()
        for cookie in payload["cookies"]:
            if not isinstance(cookie, dict):
                continue
            name = cookie.get("name")
            value = cookie.get("value")
            if not name or value is None:
                continue
            jar.set(
                str(name),
                str(value),
                domain=cookie.get("domain"),
                path=cookie.get("path") or "/",
            )
        return jar

    def delete(self, include_browser_profile: bool = False) -> dict[str, Any]:
        removed: list[str] = []
        if self.path.exists():
            self.path.unlink()
            removed.append(str(self.path))
        if include_browser_profile and self.config.auth_profile_dir.exists():
            _remove_tree(self.config.auth_profile_dir)
            removed.append(str(self.config.auth_profile_dir))
        return {"removed": removed}

    def status(self) -> CookieStatus:
        if not self.path.exists():
            return CookieStatus(
                state="MISSING",
                path=self.path,
                exists=False,
                message="Cookie file does not exist",
            )
        try:
            payload = self.load_payload()
        except CmsMcpError as exc:
            return CookieStatus(
                state="INVALID",
                path=self.path,
                exists=True,
                message=exc.message,
            )
        created_at = payload.get("created_at")
        age_seconds = None
        if isinstance(created_at, str):
            try:
                created = datetime.fromisoformat(created_at)
                age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
            except ValueError:
                pass
        return CookieStatus(
            state="PRESENT",
            path=self.path,
            exists=True,
            age_seconds=age_seconds,
            message="Cookie file is present",
        )

    def sanitized_payload(self) -> dict[str, Any]:
        return redact(self.load_payload())


def _remove_tree(path: Path) -> None:
    for child in path.iterdir():
        if child.is_dir():
            _remove_tree(child)
        else:
            child.unlink()
    path.rmdir()
