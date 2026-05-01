"""Shared fixtures.

Every test gets a clean temp cache directory so the user's real cache is
never touched and tests don't share state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from webview.config import Settings, get_settings


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("WEBVIEW_CACHE_DIR", str(cache_dir))
    monkeypatch.setenv("WEBVIEW_BACKEND", "extractive")
    get_settings.cache_clear()
    yield Settings()
    get_settings.cache_clear()


SAMPLE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <title>Sample Article</title>
  <meta name="author" content="Jane Doe">
  <meta name="description" content="A sample article about WebView v2.">
</head>
<body>
  <header><nav>Site nav · About · Contact</nav></header>
  <article>
    <h1>Sample Article</h1>
    <p>WebView v2 is a Python library for fetching, extracting, and querying
       web content with pluggable open-source LLM backends.</p>
    <p>It defaults to a zero-LLM extractive backend so it works with no setup.
       Contact the author at jane@example.com or visit https://example.com.</p>
    <p>The project was published on 2026-04-01 and costs $0 to run.</p>
  </article>
  <footer>© 2026 Example Corp</footer>
</body>
</html>
"""


@pytest.fixture
def sample_html() -> str:
    return SAMPLE_HTML
