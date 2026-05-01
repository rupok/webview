"""Pluggable LLM backends.

Pick a backend via ``WEBVIEW_BACKEND`` (or pass ``backend=`` to ``view()``):
  - ``extractive``     — no LLM, pure-Python TextRank + BM25 (default)
  - ``ollama``         — local Ollama daemon (recommended for real LLM use)
  - ``openai-compat``  — any OpenAI-compatible server (Groq, OpenRouter,
                         LM Studio, vLLM, llama.cpp server, Together free tier)
  - ``hf``             — Hugging Face Inference API (free tier)
"""

from __future__ import annotations

from webview.config import Settings, get_settings
from webview.llm.base import LLM


def get_llm(settings: Settings | None = None) -> LLM:
    """Return an LLM instance based on the active settings."""
    settings = settings or get_settings()
    backend = settings.backend

    if backend == "extractive":
        from webview.llm.extractive import ExtractiveLLM

        return ExtractiveLLM()
    if backend == "ollama":
        from webview.llm.ollama import OllamaLLM

        return OllamaLLM(base_url=settings.ollama_url, model=settings.model)
    if backend == "openai-compat":
        from webview.llm.openai_compat import OpenAICompatLLM

        return OpenAICompatLLM(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.model,
        )
    if backend == "hf":
        from webview.llm.hf import HuggingFaceLLM

        return HuggingFaceLLM(token=settings.hf_token, model=settings.model)

    raise ValueError(f"unknown backend: {backend}")


__all__ = ["LLM", "get_llm"]
