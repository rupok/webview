"""End-to-end test of view() with HTTP mocked via respx."""

from __future__ import annotations

import httpx
import respx

from webview import view


@respx.mock
def test_view_pipeline_uses_cache_on_second_call(sample_html: str):
    url = "https://example.com/test-article"
    route = respx.get(url).mock(return_value=httpx.Response(200, html=sample_html))

    page1 = view(url)
    assert page1.title == "Sample Article"
    assert "WebView v2" in page1.markdown
    assert page1.chunks

    page2 = view(url)
    assert page2.title == page1.title
    assert route.call_count == 1, "second view() should hit the cache, not the network"


@respx.mock
def test_view_refresh_bypasses_cache(sample_html: str):
    url = "https://example.com/refresh-me"
    route = respx.get(url).mock(return_value=httpx.Response(200, html=sample_html))

    view(url)
    view(url, refresh=True)
    assert route.call_count == 2


@respx.mock
def test_view_summarize_with_extractive_backend(sample_html: str):
    url = "https://example.com/summarize-me"
    respx.get(url).mock(return_value=httpx.Response(200, html=sample_html))

    page = view(url)
    summary = page.summarize(max_sentences=2)
    assert summary


@respx.mock
def test_view_ask_with_extractive_backend(sample_html: str):
    url = "https://example.com/ask-me"
    respx.get(url).mock(return_value=httpx.Response(200, html=sample_html))

    page = view(url)
    answer = page.ask("What is WebView?")
    assert "WebView" in answer or "Not found" in answer
