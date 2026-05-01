"""Jinja2 wrapper for our packaged templates.

Templates live under ``src/webview/templates/`` and are shipped with the
wheel via ``[tool.hatch.build.targets.wheel.force-include]``.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent / "templates"


def env_for(subdir: str) -> Environment:
    """Return a Jinja2 environment rooted at ``templates/<subdir>``."""
    root = TEMPLATES_DIR / subdir
    if not root.is_dir():
        raise FileNotFoundError(f"template directory missing: {root}")
    return Environment(
        loader=FileSystemLoader(str(root)),
        keep_trailing_newline=True,
        undefined=StrictUndefined,
        autoescape=False,
    )


def list_templates(subdir: str) -> list[str]:
    """List relative template paths under a templates subdir."""
    root = TEMPLATES_DIR / subdir
    out: list[str] = []
    for path in root.rglob("*.j2"):
        out.append(str(path.relative_to(root)))
    return sorted(out)
