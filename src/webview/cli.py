"""Typer CLI.

Entry point: ``webview`` (see pyproject.toml [project.scripts]).

Commands:
  fetch       URL → clean markdown
  summarize   URL → summary (works with zero LLM via extractive backend)
  ask         URL + question → answer
  extract     URL + JSON schema → structured JSON
  cache       inspect / clear the local cache
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from webview import cache as cache_mod
from webview import view
from webview.config import get_settings

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Let AI view a website. Fetch, extract, and query web content.",
)
cache_app = typer.Typer(no_args_is_help=True, help="Inspect or manage the local page cache.")
app.add_typer(cache_app, name="cache")

console = Console()
err_console = Console(stderr=True)


@app.command()
def fetch(
    url: str,
    render: Annotated[bool, typer.Option(help="Use Playwright for JS-rendered pages.")] = False,
    refresh: Annotated[bool, typer.Option(help="Bypass the cache.")] = False,
    plain: Annotated[bool, typer.Option(help="Plain markdown, no rich formatting.")] = False,
) -> None:
    """Fetch URL and print the cleaned markdown."""
    page = view(url, render=render, refresh=refresh)
    if plain or not sys.stdout.isatty():
        sys.stdout.write(str(page) + "\n")
    else:
        console.print(Markdown(str(page)))


@app.command()
def summarize(
    url: str,
    sentences: Annotated[int, typer.Option("--sentences", "-n", help="Maximum sentences.")] = 5,
    render: Annotated[bool, typer.Option(help="Use Playwright for JS-rendered pages.")] = False,
    refresh: Annotated[bool, typer.Option(help="Bypass the cache.")] = False,
) -> None:
    """Summarize the page at URL."""
    page = view(url, render=render, refresh=refresh)
    summary = page.summarize(max_sentences=sentences)
    _print_panel(page.title, summary, page.backend)


@app.command()
def ask(
    url: str,
    question: str,
    render: Annotated[bool, typer.Option(help="Use Playwright for JS-rendered pages.")] = False,
    refresh: Annotated[bool, typer.Option(help="Bypass the cache.")] = False,
) -> None:
    """Ask a question about the page at URL."""
    page = view(url, render=render, refresh=refresh)
    answer = page.ask(question)
    _print_panel(f"Q: {question}", answer, page.backend, subtitle=page.title)


@app.command()
def extract(
    url: str,
    schema: Annotated[Path, typer.Option("--schema", "-s", help="Path to JSON schema file.")],
    render: Annotated[bool, typer.Option(help="Use Playwright for JS-rendered pages.")] = False,
    refresh: Annotated[bool, typer.Option(help="Bypass the cache.")] = False,
) -> None:
    """Extract structured JSON conforming to a schema."""
    if not schema.exists():
        err_console.print(f"[red]schema file not found: {schema}[/red]")
        raise typer.Exit(2)
    schema_doc = json.loads(schema.read_text())
    page = view(url, render=render, refresh=refresh)
    result = page.extract(schema_doc)
    sys.stdout.write(json.dumps(result, indent=2) + "\n")


@cache_app.command("stats")
def cache_stats() -> None:
    """Show the local cache stats."""
    info = cache_mod.stats()
    console.print(info)


@cache_app.command("clear")
def cache_clear() -> None:
    """Clear the local cache."""
    cache_mod.clear()
    console.print("[green]cache cleared[/green]")


@cache_app.command("path")
def cache_path() -> None:
    """Print the on-disk cache path."""
    console.print(str(get_settings().cache_db_path()))


@app.command()
def info() -> None:
    """Print active configuration."""
    s = get_settings()
    console.print(
        {
            "backend": s.backend,
            "model": s.model,
            "ollama_url": s.ollama_url,
            "openai_base_url": s.openai_base_url,
            "cache_dir": str(s.cache_dir),
            "cache_ttl_seconds": s.cache_ttl_seconds,
            "max_context_tokens": s.max_context_tokens,
        }
    )


def _print_panel(title: str, body: str, backend: str, *, subtitle: str | None = None) -> None:
    panel = Panel(
        body,
        title=title,
        subtitle=f"[dim]{subtitle or ''} · backend={backend}[/dim]",
        border_style="cyan",
    )
    console.print(panel)


if __name__ == "__main__":
    app()
