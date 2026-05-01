"""Kotlin/Gradle Android project generator.

Renders the templates under ``templates/kotlin/`` into a fully buildable
Android Studio project. Works for any URL (HTTP or HTTPS) — recommended
when the site is not a PWA.

Output layout:

    <out>/
    ├── settings.gradle.kts
    ├── build.gradle.kts
    ├── gradle.properties
    ├── README.md
    ├── webview.json                 (a copy of the source config)
    └── app/
        ├── build.gradle.kts
        ├── proguard-rules.pro
        └── src/main/
            ├── AndroidManifest.xml
            ├── kotlin/<package>/MainActivity.kt
            └── res/
                ├── mipmap-*/ic_launcher.png + foreground
                ├── mipmap-anydpi-v26/ic_launcher.xml
                ├── values/{strings,colors,themes}.xml
                └── xml/{network_security_config,data_extraction_rules}.xml
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from webview.config import CONFIG_FILENAME, AppConfig
from webview.icons import (
    load_or_generate_source,
    write_adaptive_icon,
    write_legacy_mipmaps,
)
from webview.render import env_for


@dataclass(slots=True)
class KotlinBuildResult:
    output_dir: Path
    files: list[Path]


def build_kotlin_project(config: AppConfig, output_dir: Path) -> KotlinBuildResult:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    env = env_for("kotlin")
    context = _template_context(config)
    written: list[Path] = []

    file_map = {
        "settings.gradle.kts.j2": "settings.gradle.kts",
        "build.gradle.kts.j2": "build.gradle.kts",
        "gradle.properties.j2": "gradle.properties",
        "README.md.j2": "README.md",
        "app/build.gradle.kts.j2": "app/build.gradle.kts",
        "app/proguard-rules.pro.j2": "app/proguard-rules.pro",
        "app/src/main/AndroidManifest.xml.j2": "app/src/main/AndroidManifest.xml",
        "app/src/main/res/values/strings.xml.j2": "app/src/main/res/values/strings.xml",
        "app/src/main/res/values/colors.xml.j2": "app/src/main/res/values/colors.xml",
        "app/src/main/res/values/themes.xml.j2": "app/src/main/res/values/themes.xml",
        "app/src/main/res/xml/network_security_config.xml.j2": "app/src/main/res/xml/network_security_config.xml",
        "app/src/main/res/xml/data_extraction_rules.xml.j2": "app/src/main/res/xml/data_extraction_rules.xml",
    }

    for template, relative in file_map.items():
        rendered = env.get_template(template).render(**context)
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered)
        written.append(target)

    main_activity_dir = output_dir / "app" / "src" / "main" / "kotlin" / Path(*config.package.split("."))
    main_activity_dir.mkdir(parents=True, exist_ok=True)
    rendered = env.get_template("app/src/main/kotlin/MainActivity.kt.j2").render(**context)
    target = main_activity_dir / "MainActivity.kt"
    target.write_text(rendered)
    written.append(target)

    icon_path = Path(config.icon).resolve() if config.icon else None
    source_icon = load_or_generate_source(
        icon_path,
        app_name=config.name,
        color=config.theme_color,
    )
    res_dir = output_dir / "app" / "src" / "main" / "res"
    written.extend(write_legacy_mipmaps(source_icon, res_dir))
    written.extend(write_adaptive_icon(source_icon, res_dir, background_color=config.background_color))

    config_copy = output_dir / CONFIG_FILENAME
    config.save(config_copy)
    written.append(config_copy)

    return KotlinBuildResult(output_dir=output_dir, files=written)


def _template_context(config: AppConfig) -> dict:
    return {
        "name": config.name,
        "package": config.package,
        "url": config.url,
        "host": config.host,
        "is_https": config.is_https,
        "version_name": config.version_name,
        "version_code": config.version_code,
        "min_sdk": config.min_sdk,
        "target_sdk": config.target_sdk,
        "theme_color": config.theme_color,
        "background_color": config.background_color,
        "theme_color_int": _hex_to_int(config.theme_color),
        "orientation": config.orientation,
        "allow_external_links": config.allow_external_links,
        "app_user_agent": f"WebViewApp/{config.version_name}",
    }


def _hex_to_int(hex_color: str) -> str:
    """Return a Kotlin Int literal for an opaque ARGB color."""
    rgb = int(hex_color.lstrip("#"), 16)
    argb = 0xFF000000 | rgb
    return f"0x{argb:08X}.toInt()"
