"""GitHub Actions workflow generator.

Writes ``.github/workflows/build.yml`` so users without a local Android
toolchain can push and have the APK/AAB built in CI.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from webview.config import AppConfig
from webview.render import env_for

WorkflowPath = Literal["kotlin", "twa"]


def write_github_actions_workflow(
    config: AppConfig,
    output_dir: Path,
    *,
    path: WorkflowPath = "kotlin",
) -> Path:
    if path not in ("kotlin", "twa"):
        raise ValueError(f"path must be 'kotlin' or 'twa', got {path!r}")
    output_dir = output_dir.resolve()
    workflow_path = output_dir / ".github" / "workflows" / "build.yml"
    workflow_path.parent.mkdir(parents=True, exist_ok=True)

    env = env_for("ci")
    rendered = env.get_template("build.yml.j2").render(
        path=path,
        name_slug=_slugify(config.name),
    )
    workflow_path.write_text(rendered)
    return workflow_path


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "app"
