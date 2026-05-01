from __future__ import annotations

import httpx
import respx

from webview import detect

PWA_HTML = """
<!doctype html>
<html>
<head>
  <link rel="manifest" href="/manifest.webmanifest">
  <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js');
    }
  </script>
</head>
<body>hi</body>
</html>
"""

PWA_MANIFEST = {
    "name": "Example PWA",
    "short_name": "Example",
    "start_url": "/",
    "display": "standalone",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}

PLAIN_HTML = "<!doctype html><html><body>plain old site</body></html>"


@respx.mock
def test_detect_pwa_recommends_twa():
    respx.get("https://example.com/").mock(return_value=httpx.Response(200, text=PWA_HTML))
    respx.get("https://example.com/manifest.webmanifest").mock(
        return_value=httpx.Response(200, json=PWA_MANIFEST)
    )
    result = detect.detect("https://example.com/")
    assert result.recommended == "twa"
    assert result.has_manifest is True
    assert result.has_service_worker_hint is True


@respx.mock
def test_detect_plain_site_recommends_kotlin():
    respx.get("https://plain.example.com/").mock(return_value=httpx.Response(200, text=PLAIN_HTML))
    result = detect.detect("https://plain.example.com/")
    assert result.recommended == "kotlin"
    assert result.has_manifest is False


def test_detect_http_url_recommends_kotlin_without_network():
    result = detect.detect("http://intranet.local/")
    assert result.recommended == "kotlin"
    assert result.is_https is False


@respx.mock
def test_detect_handles_unreachable_url():
    respx.get("https://broken.example/").mock(side_effect=httpx.ConnectError("nope"))
    result = detect.detect("https://broken.example/")
    assert result.recommended == "kotlin"


@respx.mock
def test_detect_manifest_missing_required_fields():
    bad_manifest = {"name": "X"}  # no start_url, no icons
    html = '<link rel="manifest" href="/m.json">'
    respx.get("https://bad.example/").mock(return_value=httpx.Response(200, text=html))
    respx.get("https://bad.example/m.json").mock(return_value=httpx.Response(200, json=bad_manifest))
    result = detect.detect("https://bad.example/")
    assert result.recommended == "kotlin"
    assert result.has_manifest is True
