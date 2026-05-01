"""Runtime configuration loaded from environment variables.

All settings are prefixed with ``WEBVIEW_``. The defaults aim to work on a
fresh machine with zero setup: extractive backend, on-disk cache under the
user's cache directory, and conservative timeouts.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from platformdirs import user_cache_dir
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Backend = Literal["extractive", "ollama", "openai-compat", "hf"]


class Settings(BaseSettings):
    """User-tunable configuration. Construct once via ``get_settings()``."""

    model_config = SettingsConfigDict(
        env_prefix="WEBVIEW_",
        env_file=".env",
        extra="ignore",
    )

    backend: Backend = "extractive"
    model: str = "llama3.2"

    ollama_url: str = "http://localhost:11434"
    openai_base_url: str = "http://localhost:8080/v1"
    openai_api_key: str = "sk-no-key-required"
    hf_token: str = ""

    fetch_timeout: float = 20.0
    fetch_user_agent: str = (
        "WebView/2.0 (+https://github.com/rupok/webview; AI content reader)"
    )
    fetch_max_bytes: int = 5_000_000

    cache_dir: Path = Field(default_factory=lambda: Path(user_cache_dir("webview")))
    cache_ttl_seconds: int = 24 * 60 * 60

    chunk_tokens: int = 1200
    chunk_overlap_tokens: int = 100
    max_context_tokens: int = 8000

    def cache_db_path(self) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / "pages.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
