from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from webview.config import AppConfig


def test_basic_config_roundtrip(tmp_path: Path, basic_config: AppConfig):
    target = tmp_path / "webview.json"
    basic_config.save(target)
    loaded = AppConfig.load(target)
    assert loaded == basic_config


def test_find_and_load_walks_up(tmp_path: Path, basic_config: AppConfig):
    parent = tmp_path / "project"
    nested = parent / "deep" / "nested"
    nested.mkdir(parents=True)
    basic_config.save(parent / "webview.json")
    loaded = AppConfig.find_and_load(start=nested)
    assert loaded.name == basic_config.name


def test_invalid_package_rejected():
    with pytest.raises(ValidationError):
        AppConfig(name="x", url="https://x.com", package="NotReverseDNS")


def test_invalid_color_rejected():
    with pytest.raises(ValidationError):
        AppConfig(name="x", url="https://x.com", package="com.x.y", theme_color="red")


def test_invalid_url_rejected():
    with pytest.raises(ValidationError):
        AppConfig(name="x", url="ftp://x.com", package="com.x.y")


def test_host_property(basic_config: AppConfig):
    assert basic_config.host == "example.com"
    assert basic_config.is_https is True


def test_save_writes_valid_json(tmp_path: Path, basic_config: AppConfig):
    target = tmp_path / "webview.json"
    basic_config.save(target)
    data = json.loads(target.read_text())
    assert data["package"] == "com.example.app"
