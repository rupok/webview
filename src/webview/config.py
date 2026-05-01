"""User-facing app configuration.

A single ``webview.json`` in the user's project drives everything: app
name, package id, target URL, theme colors, optional icon. Builders read
this and emit the right files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

CONFIG_FILENAME = "webview.json"


class AppConfig(BaseModel):
    """Everything a builder needs to produce an Android app."""

    name: str = Field(..., description="Display name shown under the launcher icon.")
    url: str = Field(..., description="Website to load. Must be HTTPS for TWA.")
    package: str = Field(
        ...,
        description="Android applicationId, e.g. com.example.myapp. Must be reverse-DNS.",
    )
    version_name: str = "1.0.0"
    version_code: int = 1
    theme_color: str = Field("#1976D2", description="Toolbar / status bar color, hex.")
    background_color: str = Field("#FFFFFF", description="Splash and adaptive-icon background, hex.")
    min_sdk: int = 24
    target_sdk: int = 35
    icon: str | None = Field(
        None,
        description="Path to a square PNG (>= 512x512 recommended) used to derive launcher icons.",
    )
    orientation: Literal["unspecified", "portrait", "landscape"] = "unspecified"
    allow_external_links: bool = Field(
        False,
        description="If false, off-domain links open in the user's real browser (recommended).",
    )

    @field_validator("package")
    @classmethod
    def _validate_package(cls, v: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", v):
            raise ValueError(
                f"package must be reverse-DNS lowercase, e.g. com.example.myapp (got {v!r})"
            )
        return v

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"url must be http(s), got {v!r}")
        if not parsed.netloc:
            raise ValueError(f"url has no host: {v!r}")
        return v

    @field_validator("theme_color", "background_color")
    @classmethod
    def _validate_color(cls, v: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            raise ValueError(f"color must be 6-digit hex like #1976D2 (got {v!r})")
        return v.upper()

    @property
    def host(self) -> str:
        return urlparse(self.url).netloc

    @property
    def is_https(self) -> bool:
        return urlparse(self.url).scheme == "https"

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.model_dump(), indent=2) + "\n")

    @classmethod
    def load(cls, path: Path) -> AppConfig:
        return cls.model_validate_json(path.read_text())

    @classmethod
    def find_and_load(cls, start: Path | None = None) -> AppConfig:
        """Walk up from ``start`` looking for ``webview.json``."""
        current = (start or Path.cwd()).resolve()
        for candidate in [current, *current.parents]:
            cfg = candidate / CONFIG_FILENAME
            if cfg.exists():
                return cls.load(cfg)
        raise FileNotFoundError(
            f"no {CONFIG_FILENAME} found in {current} or any parent. Run `webview init <url>` first."
        )
