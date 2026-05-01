from __future__ import annotations

import pytest

from webview.config import AppConfig


@pytest.fixture
def basic_config() -> AppConfig:
    return AppConfig(
        name="Example",
        url="https://example.com/",
        package="com.example.app",
        theme_color="#1976D2",
        background_color="#FFFFFF",
    )


@pytest.fixture
def http_config() -> AppConfig:
    return AppConfig(
        name="Intranet Tool",
        url="http://intranet.local/",
        package="local.intranet.tool",
    )
