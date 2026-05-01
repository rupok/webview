"""Probe a URL to decide which builder path fits.

The hierarchy:

  1. If the site is HTTPS *and* serves a valid PWA manifest with the
     required fields, recommend the **TWA** path. TWA is Google's
     blessed Play-Store path and gives full Chrome rendering.

  2. Otherwise recommend the **Kotlin** path, which generates a
     standalone WebView app project — works for any site, including
     plain HTTP, intranets, and pages without a manifest.

The detection is best-effort. We only fail closed (recommend Kotlin)
when something definitely disqualifies TWA.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

Path = Literal["twa", "kotlin"]

USER_AGENT = "WebView/2.0 (+https://github.com/rupok/webview; site probe)"


@dataclass(slots=True)
class DetectionResult:
    recommended: Path
    is_https: bool
    has_manifest: bool
    has_service_worker_hint: bool
    manifest_url: str | None
    manifest: dict | None
    reasons: list[str]


def detect(url: str, *, timeout: float = 10.0) -> DetectionResult:
    parsed = urlparse(url)
    is_https = parsed.scheme == "https"
    reasons: list[str] = []

    if not is_https:
        reasons.append("URL is not HTTPS — TWA requires HTTPS, falling back to Kotlin path.")
        return DetectionResult(
            recommended="kotlin",
            is_https=False,
            has_manifest=False,
            has_service_worker_hint=False,
            manifest_url=None,
            manifest=None,
            reasons=reasons,
        )

    try:
        html = _get(url, timeout=timeout)
    except _ProbeError as exc:
        reasons.append(f"could not fetch page ({exc}); falling back to Kotlin path.")
        return DetectionResult(
            recommended="kotlin",
            is_https=is_https,
            has_manifest=False,
            has_service_worker_hint=False,
            manifest_url=None,
            manifest=None,
            reasons=reasons,
        )

    soup = BeautifulSoup(html, "html.parser")
    manifest_url = _find_manifest(soup, base=url)
    has_sw_hint = _looks_like_it_uses_a_service_worker(html)

    manifest: dict | None = None
    if manifest_url:
        try:
            manifest_text = _get(manifest_url, timeout=timeout)
            manifest = json.loads(manifest_text)
        except (_ProbeError, json.JSONDecodeError) as exc:
            reasons.append(f"manifest at {manifest_url} unreadable ({exc}).")
            manifest = None

    if manifest and _is_valid_pwa_manifest(manifest):
        reasons.append("HTTPS + valid PWA manifest detected → TWA path is best.")
        if not has_sw_hint:
            reasons.append(
                "no obvious service-worker registration found — TWA still works, "
                "but offline/installable behavior may be limited."
            )
        return DetectionResult(
            recommended="twa",
            is_https=True,
            has_manifest=True,
            has_service_worker_hint=has_sw_hint,
            manifest_url=manifest_url,
            manifest=manifest,
            reasons=reasons,
        )

    if manifest_url:
        reasons.append("manifest linked but missing required PWA fields → Kotlin path.")
    else:
        reasons.append("no PWA manifest linked → Kotlin path.")

    return DetectionResult(
        recommended="kotlin",
        is_https=is_https,
        has_manifest=bool(manifest_url),
        has_service_worker_hint=has_sw_hint,
        manifest_url=manifest_url,
        manifest=manifest,
        reasons=reasons,
    )


class _ProbeError(RuntimeError):
    pass


def _get(url: str, *, timeout: float) -> str:
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        raise _ProbeError(str(exc)) from exc
    if response.status_code >= 400:
        raise _ProbeError(f"HTTP {response.status_code}")
    return response.text


def _find_manifest(soup: BeautifulSoup, *, base: str) -> str | None:
    for link in soup.find_all("link"):
        rel = link.get("rel")
        if not rel:
            continue
        rel_values = rel if isinstance(rel, list) else [rel]
        if not any(r.lower() == "manifest" for r in rel_values):
            continue
        href = link.get("href")
        if href:
            return urljoin(base, href)
    return None


def _is_valid_pwa_manifest(manifest: dict) -> bool:
    if not isinstance(manifest, dict):
        return False
    if not (manifest.get("name") or manifest.get("short_name")):
        return False
    if not manifest.get("start_url"):
        return False
    icons = manifest.get("icons") or []
    if not isinstance(icons, list) or not icons:
        return False
    return any(_looks_like_large_icon(icon) for icon in icons)


def _looks_like_large_icon(icon: dict) -> bool:
    if not isinstance(icon, dict):
        return False
    sizes = (icon.get("sizes") or "").split()
    for s in sizes:
        if "x" not in s:
            continue
        try:
            w, h = (int(p) for p in s.split("x"))
        except ValueError:
            continue
        if w >= 192 and h >= 192:
            return True
    return False


def _looks_like_it_uses_a_service_worker(html: str) -> bool:
    needle = "serviceworker.register" if False else "serviceWorker.register"
    return needle in html or "navigator.serviceWorker" in html
