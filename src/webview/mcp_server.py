"""MCP server — exposes WebView as tools for Claude Code, Claude Desktop,
or any MCP-aware client.

Run with:  ``webview-mcp``  (after ``pip install 'webview[mcp]'``)

Configure in Claude Code:

    {
      "mcpServers": {
        "webview": {"command": "webview-mcp"}
      }
    }
"""

from __future__ import annotations

import json
from typing import Any

from webview import view
from webview.config import get_settings


def _build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit(
            "MCP support requires the 'mcp' extra: pip install 'webview[mcp]'"
        ) from exc

    server = FastMCP("webview")

    @server.tool()
    def fetch_page(url: str, render: bool = False) -> str:
        """Fetch a URL and return cleaned markdown of the main content."""
        page = view(url, render=render)
        return str(page)

    @server.tool()
    def summarize_page(url: str, max_sentences: int = 5, render: bool = False) -> str:
        """Summarize the main content of the page at URL."""
        page = view(url, render=render)
        return page.summarize(max_sentences=max_sentences)

    @server.tool()
    def ask_page(url: str, question: str, render: bool = False) -> str:
        """Ask a question about the page at URL."""
        page = view(url, render=render)
        return page.ask(question)

    @server.tool()
    def extract_page(url: str, schema_json: str, render: bool = False) -> dict[str, Any]:
        """Extract structured JSON from the page at URL.

        ``schema_json`` is a JSON-encoded schema describing the desired fields.
        """
        schema = json.loads(schema_json)
        page = view(url, render=render)
        return page.extract(schema)

    @server.tool()
    def webview_info() -> dict[str, Any]:
        """Return the current backend / model / cache configuration."""
        s = get_settings()
        return {
            "backend": s.backend,
            "model": s.model,
            "cache_dir": str(s.cache_dir),
        }

    return server


def main() -> None:
    server = _build_server()
    server.run()


if __name__ == "__main__":
    main()
