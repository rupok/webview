"""Trusted Web Activity (TWA) project generator.

Produces a Bubblewrap-ready directory containing:

    <out>/
    ├── twa-manifest.json   ← consumed by `bubblewrap init`
    ├── icon.png            ← 512x512 launcher source
    ├── README.md           ← step-by-step build instructions
    └── webview.json        ← copy of the source config

Bubblewrap takes the manifest and produces a signed AAB/APK. We don't
re-implement Bubblewrap because it does this well already and it is the
upstream reference TWA toolchain.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from webview.config import CONFIG_FILENAME, AppConfig
from webview.icons import load_or_generate_source
from webview.render import env_for


@dataclass(slots=True)
class TWABuildResult:
    output_dir: Path
    files: list[Path]
    bubblewrap_command: str


class TWAUnsupported(RuntimeError):
    """Raised when the configured site cannot ship as a TWA."""


def build_twa_project(
    config: AppConfig,
    output_dir: Path,
    *,
    web_manifest_url: str | None = None,
) -> TWABuildResult:
    if not config.is_https:
        raise TWAUnsupported(
            "TWA requires HTTPS. Use --kotlin for HTTP / intranet sites."
        )

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    env = env_for("twa")
    context = _template_context(config, web_manifest_url=web_manifest_url)

    for template, relative in (
        ("twa-manifest.json.j2", "twa-manifest.json"),
        ("README.md.j2", "README.md"),
    ):
        rendered = env.get_template(template).render(**context)
        target = output_dir / relative
        target.write_text(rendered)
        written.append(target)

    icon_path = Path(config.icon).resolve() if config.icon else None
    icon = load_or_generate_source(icon_path, app_name=config.name, color=config.theme_color)
    icon_target = output_dir / "icon.png"
    icon.save(icon_target)
    written.append(icon_target)

    config_copy = output_dir / CONFIG_FILENAME
    config.save(config_copy)
    written.append(config_copy)

    return TWABuildResult(
        output_dir=output_dir,
        files=written,
        bubblewrap_command=f"cd {output_dir} && bubblewrap init --manifest=./twa-manifest.json && bubblewrap build",
    )


def _template_context(config: AppConfig, *, web_manifest_url: str | None) -> dict:
    parsed = urlparse(config.url)
    start_path = parsed.path or "/"
    if parsed.query:
        start_path = f"{start_path}?{parsed.query}"
    return {
        "name": config.name,
        "package": config.package,
        "url": config.url,
        "host": config.host,
        "start_path": start_path,
        "version_name": config.version_name,
        "version_code": config.version_code,
        "theme_color": config.theme_color,
        "background_color": config.background_color,
        "min_sdk": config.min_sdk,
        "orientation": config.orientation,
        "web_manifest_url": web_manifest_url,
    }
