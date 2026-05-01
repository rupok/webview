from __future__ import annotations

from pathlib import Path

from webview.builders import build_kotlin_project
from webview.config import AppConfig


def test_kotlin_project_layout(tmp_path: Path, basic_config: AppConfig):
    out = tmp_path / "app"
    result = build_kotlin_project(basic_config, out)

    expected = [
        "settings.gradle.kts",
        "build.gradle.kts",
        "gradle.properties",
        "README.md",
        "webview.json",
        "app/build.gradle.kts",
        "app/proguard-rules.pro",
        "app/src/main/AndroidManifest.xml",
        "app/src/main/res/values/strings.xml",
        "app/src/main/res/values/colors.xml",
        "app/src/main/res/values/themes.xml",
        "app/src/main/res/values/ic_launcher_background.xml",
        "app/src/main/res/xml/network_security_config.xml",
        "app/src/main/res/xml/data_extraction_rules.xml",
        "app/src/main/res/mipmap-mdpi/ic_launcher.png",
        "app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.png",
        "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml",
        "app/src/main/kotlin/com/example/app/MainActivity.kt",
    ]
    for rel in expected:
        assert (out / rel).exists(), f"missing: {rel}"
    assert result.output_dir == out.resolve()


def test_kotlin_main_activity_has_url_and_package(tmp_path: Path, basic_config: AppConfig):
    out = tmp_path / "app"
    build_kotlin_project(basic_config, out)
    activity = (out / "app/src/main/kotlin/com/example/app/MainActivity.kt").read_text()
    assert "package com.example.app" in activity
    assert 'HOME_URL = "https://example.com/"' in activity
    assert 'HOME_HOST = "example.com"' in activity


def test_kotlin_manifest_uses_https_for_https_url(tmp_path: Path, basic_config: AppConfig):
    out = tmp_path / "app"
    build_kotlin_project(basic_config, out)
    manifest = (out / "app/src/main/AndroidManifest.xml").read_text()
    assert 'android:usesCleartextTraffic="false"' in manifest
    assert '<data android:scheme="https" android:host="example.com"' in manifest


def test_kotlin_manifest_allows_cleartext_for_http_url(tmp_path: Path, http_config: AppConfig):
    out = tmp_path / "app"
    build_kotlin_project(http_config, out)
    manifest = (out / "app/src/main/AndroidManifest.xml").read_text()
    assert 'android:usesCleartextTraffic="true"' in manifest


def test_kotlin_strings_uses_app_name(tmp_path: Path, basic_config: AppConfig):
    out = tmp_path / "app"
    build_kotlin_project(basic_config, out)
    strings = (out / "app/src/main/res/values/strings.xml").read_text()
    assert "<string name=\"app_name\">Example</string>" in strings


def test_kotlin_build_gradle_uses_package_and_sdks(tmp_path: Path, basic_config: AppConfig):
    out = tmp_path / "app"
    build_kotlin_project(basic_config, out)
    gradle = (out / "app/build.gradle.kts").read_text()
    assert 'namespace = "com.example.app"' in gradle
    assert 'applicationId = "com.example.app"' in gradle
    assert "compileSdk = 35" in gradle
    assert "minSdk = 24" in gradle
