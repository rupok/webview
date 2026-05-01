from __future__ import annotations

from pathlib import Path

import pytest

from webview.builders import write_github_actions_workflow
from webview.config import AppConfig


def test_ci_kotlin_workflow(tmp_path: Path, basic_config: AppConfig):
    write_github_actions_workflow(basic_config, tmp_path, path="kotlin")
    workflow = (tmp_path / ".github/workflows/build.yml").read_text()
    assert "webview build --kotlin" in workflow
    assert "./gradlew assembleRelease" in workflow
    assert "example-apk" in workflow
    assert "Bubblewrap" not in workflow


def test_ci_twa_workflow(tmp_path: Path, basic_config: AppConfig):
    write_github_actions_workflow(basic_config, tmp_path, path="twa")
    workflow = (tmp_path / ".github/workflows/build.yml").read_text()
    assert "webview build --twa" in workflow
    assert "@bubblewrap/cli" in workflow
    assert "example-aab" in workflow


def test_ci_rejects_unknown_path(tmp_path: Path, basic_config: AppConfig):
    with pytest.raises(ValueError, match="kotlin"):
        write_github_actions_workflow(basic_config, tmp_path, path="capacitor")  # type: ignore[arg-type]
