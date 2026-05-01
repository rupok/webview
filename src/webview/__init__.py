"""WebView — let AI view a website.

A small library for fetching web pages, extracting clean content, and
querying that content with pluggable open-source LLM backends (Ollama,
OpenAI-compatible servers, Hugging Face, or a zero-LLM extractive fallback).
"""

from webview.config import Settings, get_settings
from webview.core import Page, view

__version__ = "2.0.0"
__all__ = ["Page", "Settings", "__version__", "get_settings", "view"]
