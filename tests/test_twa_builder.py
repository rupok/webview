from __future__ import annotations

import json
from pathlib import Path

import pytest

from webview.builders import build_twa_project
from webview.builders.twa import TWAUnsupported
from webview.config import AppConfig


def test_twa_project_writes_manifest_and_icon(tmp_path: Path, basic_config: AppConfig):
    out = tmp_path / "twa"
    result = build_twa_project(basic_config, out)

    manifest = json.loads((out / "twa-manifest.json").read_text())
    assert manifest["packageId"] == "com.example.app"
    assert manifest["host"] == "example.com"
    assert manifest["startUrl"] == "/"
    assert manifest["themeColor"] == "#1976D2"

    assert (out / "icon.png").exists()
    assert (out / "README.md").exists()
    assert (out / "webview.json").exists()
    assert "bubblewrap" in result.bubblewrap_command


def test_twa_rejects_http_urls(tmp_path: Path, http_config: AppConfig):
    with pytest.raises(TWAUnsupported, match="HTTPS"):
        build_twa_project(http_config, tmp_path / "twa")
