"""Typer CLI.

Commands:

  webview init <url>          Interactive: write webview.json
  webview detect [<url>]      Probe a URL and recommend a build path
  webview build [path opts]   Generate a project (kotlin / twa)
  webview ci                  Write a GitHub Actions workflow
  webview info                Show the active config
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from webview import detect as detect_mod
from webview.builders import (
    build_kotlin_project,
    build_twa_project,
    write_github_actions_workflow,
)
from webview.builders.twa import TWAUnsupported
from webview.config import CONFIG_FILENAME, AppConfig

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Turn your website into a real Android app. URL in, signed APK/AAB out.",
)
console = Console()
err_console = Console(stderr=True)


@app.command()
def init(
    url: str,
    name: Annotated[str | None, typer.Option(help="Display name shown under the launcher icon.")] = None,
    package: Annotated[str | None, typer.Option(help="Reverse-DNS package id, e.g. com.example.myapp")] = None,
    theme_color: Annotated[str, typer.Option(help="Hex color, e.g. #1976D2")] = "#1976D2",
    background_color: Annotated[str, typer.Option(help="Hex color for splash background")] = "#FFFFFF",
    icon: Annotated[Path | None, typer.Option(help="Path to a square PNG (>=512px).")] = None,
    output: Annotated[Path, typer.Option(help="Where to write webview.json.")] = Path("."),
) -> None:
    """Write a webview.json describing the app to build."""
    inferred_name = name or _name_from_url(url)
    inferred_package = package or _package_from_url(url)

    config = AppConfig(
        name=inferred_name,
        url=url,
        package=inferred_package,
        theme_color=theme_color,
        background_color=background_color,
        icon=str(icon.resolve()) if icon else None,
    )

    output.mkdir(parents=True, exist_ok=True)
    target = output / CONFIG_FILENAME
    config.save(target)
    console.print(f"[green]wrote {target}[/green]")
    _print_config(config)
    console.print()
    console.print("Next: [bold]webview build[/bold] (auto-picks a path) or [bold]webview detect[/bold].")


@app.command()
def detect(
    url: Annotated[str | None, typer.Argument(help="URL to probe. Defaults to the URL in webview.json.")] = None,
) -> None:
    """Probe a URL and recommend a build path (twa or kotlin)."""
    target_url = url or _load_config().url
    result = detect_mod.detect(target_url)
    table = Table(title=f"Probe: {target_url}", show_header=False)
    table.add_row("Recommended path", f"[bold green]{result.recommended}[/bold green]")
    table.add_row("HTTPS", str(result.is_https))
    table.add_row("PWA manifest", str(result.has_manifest))
    table.add_row("Service worker hint", str(result.has_service_worker_hint))
    if result.manifest_url:
        table.add_row("Manifest URL", result.manifest_url)
    console.print(table)
    for reason in result.reasons:
        console.print(f"  · {reason}", style="dim")


@app.command()
def build(
    kotlin: Annotated[bool, typer.Option("--kotlin", help="Force Kotlin WebView path.")] = False,
    twa: Annotated[bool, typer.Option("--twa", help="Force TWA / Bubblewrap path.")] = False,
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory for the generated project.")] = Path("./out"),
) -> None:
    """Generate a buildable Android project from webview.json."""
    if kotlin and twa:
        err_console.print("[red]choose one of --kotlin / --twa, not both[/red]")
        raise typer.Exit(2)

    config = _load_config()

    if not (kotlin or twa):
        result = detect_mod.detect(config.url)
        chosen = result.recommended
        console.print(f"auto-detected: [bold]{chosen}[/bold]")
        for reason in result.reasons:
            console.print(f"  · {reason}", style="dim")
    else:
        chosen = "kotlin" if kotlin else "twa"

    if chosen == "twa":
        try:
            twa_result = build_twa_project(config, output)
        except TWAUnsupported as exc:
            err_console.print(f"[red]TWA path unsupported:[/red] {exc}")
            err_console.print("Use [bold]--kotlin[/bold] instead.")
            raise typer.Exit(1) from None
        _print_build_result("TWA", twa_result.output_dir, len(twa_result.files))
        console.print(
            Panel(
                f"Next: [bold]{twa_result.bubblewrap_command}[/bold]\n\n"
                "(Requires Node.js + JDK 17 + @bubblewrap/cli)",
                title="Build the AAB",
            )
        )
        return

    kotlin_result = build_kotlin_project(config, output)
    _print_build_result("Kotlin", kotlin_result.output_dir, len(kotlin_result.files))
    console.print(
        Panel(
            f"Next: [bold]cd {kotlin_result.output_dir} && ./gradlew assembleRelease[/bold]\n\n"
            "(Requires JDK 17 + Android SDK)",
            title="Build the APK",
        )
    )


@app.command()
def ci(
    path: Annotated[str, typer.Option(help="kotlin or twa")] = "kotlin",
    output: Annotated[Path, typer.Option("--output", "-o", help="Repo root.")] = Path("."),
) -> None:
    """Write .github/workflows/build.yml so the APK is built in CI."""
    if path not in ("kotlin", "twa"):
        err_console.print(f"[red]path must be 'kotlin' or 'twa', got {path!r}[/red]")
        raise typer.Exit(2)
    config = _load_config()
    workflow = write_github_actions_workflow(config, output, path=path)  # type: ignore[arg-type]
    console.print(f"[green]wrote {workflow}[/green]")
    console.print("Push to GitHub and the workflow will build the app on each commit.")


@app.command()
def info() -> None:
    """Show the active webview.json."""
    _print_config(_load_config())


def _load_config() -> AppConfig:
    try:
        return AppConfig.find_and_load()
    except FileNotFoundError as exc:
        err_console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from None


def _print_config(config: AppConfig) -> None:
    table = Table(title=CONFIG_FILENAME, show_header=False)
    table.add_row("name", config.name)
    table.add_row("url", config.url)
    table.add_row("package", config.package)
    table.add_row("version", f"{config.version_name} ({config.version_code})")
    table.add_row("theme color", config.theme_color)
    table.add_row("background", config.background_color)
    table.add_row("min / target SDK", f"{config.min_sdk} / {config.target_sdk}")
    table.add_row("icon", config.icon or "(generated letter tile)")
    console.print(table)


def _print_build_result(label: str, output_dir: Path, file_count: int) -> None:
    console.print(f"[green]wrote {label} project: {output_dir} ({file_count} files)[/green]")


def _name_from_url(url: str) -> str:
    host = urlparse(url).netloc
    base = host.removeprefix("www.").split(".")[0]
    return base.replace("-", " ").title() or "WebView App"


def _package_from_url(url: str) -> str:
    host = urlparse(url).netloc.removeprefix("www.")
    parts = [p for p in host.split(".") if p and p[0].isalpha()]
    if len(parts) < 2:
        parts = ["app", "webview", parts[0] if parts else "generated"]
    parts = [re.sub(r"[^a-z0-9]", "", p.lower()) or "x" for p in parts]
    if not parts[0][0].isalpha():
        parts[0] = "app" + parts[0]
    return ".".join(reversed(parts))


if __name__ == "__main__":
    app()
