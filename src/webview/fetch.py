"""HTTP fetcher.

Static-first: uses httpx for the common case. The Playwright extra is loaded
lazily when ``render=True`` is requested, so users without it installed never
pay the import cost.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from webview.config import get_settings


class FetchError(RuntimeError):
    """Raised when a URL cannot be retrieved."""


@dataclass(slots=True)
class FetchResult:
    url: str
    final_url: str
    status: int
    html: str
    content_type: str
    etag: str | None


def fetch(url: str, *, render: bool = False) -> FetchResult:
    """Retrieve a URL and return the raw HTML plus metadata.

    With ``render=False`` (default) we issue a single GET via httpx. With
    ``render=True`` we use Playwright to execute JavaScript before reading
    the rendered DOM — useful for SPAs but requires the ``playwright`` extra.
    """
    if render:
        return _fetch_rendered(url)
    return _fetch_static(url)


def _fetch_static(url: str) -> FetchResult:
    settings = get_settings()
    headers = {
        "User-Agent": settings.fetch_user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=settings.fetch_timeout,
            headers=headers,
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise FetchError(f"network error fetching {url}: {exc}") from exc

    if response.status_code >= 400:
        raise FetchError(f"HTTP {response.status_code} fetching {url}")

    body = response.content[: settings.fetch_max_bytes]
    encoding = response.encoding or "utf-8"
    try:
        html = body.decode(encoding, errors="replace")
    except LookupError:
        html = body.decode("utf-8", errors="replace")

    return FetchResult(
        url=url,
        final_url=str(response.url),
        status=response.status_code,
        html=html,
        content_type=response.headers.get("content-type", ""),
        etag=response.headers.get("etag"),
    )


def _fetch_rendered(url: str) -> FetchResult:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError(
            "render=True requires the 'playwright' extra: pip install 'webview[playwright]' "
            "&& playwright install chromium"
        ) from exc

    settings = get_settings()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(user_agent=settings.fetch_user_agent)
            page = context.new_page()
            response = page.goto(url, timeout=settings.fetch_timeout * 1000)
            page.wait_for_load_state("networkidle", timeout=settings.fetch_timeout * 1000)
            html = page.content()
            final_url = page.url
            status = response.status if response else 200
        finally:
            browser.close()

    return FetchResult(
        url=url,
        final_url=final_url,
        status=status,
        html=html,
        content_type="text/html",
        etag=None,
    )
