"""Ollama backend — local, free, no signup.

Setup:
  1. Install Ollama from https://ollama.com
  2. ``ollama pull llama3.2`` (or any other model)
  3. ``export WEBVIEW_BACKEND=ollama``

Hits Ollama's native /api/chat endpoint so we don't need an extra dependency.
"""

from __future__ import annotations

import json

import httpx

from webview.llm._prompts import (
    ASK_SYSTEM,
    EXTRACT_SYSTEM,
    SUMMARIZE_SYSTEM,
    ask_user,
    extract_user,
    summarize_user,
)


class OllamaBackendError(RuntimeError):
    pass


class OllamaLLM:
    name = "ollama"

    def __init__(self, base_url: str, model: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def summarize(self, text: str, *, max_sentences: int = 5) -> str:
        return self._chat(SUMMARIZE_SYSTEM, summarize_user(text, max_sentences))

    def ask(self, question: str, context: str) -> str:
        return self._chat(ASK_SYSTEM, ask_user(question, context))

    def extract_json(self, schema: dict, context: str) -> dict:
        raw = self._chat(EXTRACT_SYSTEM, extract_user(schema, context), json_mode=True)
        return _parse_json(raw)

    def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        payload: dict = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0.2},
        }
        if json_mode:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise OllamaBackendError(
                f"could not reach Ollama at {self.base_url}: {exc}. "
                "Is the daemon running? Try: ollama serve"
            ) from exc

        if response.status_code != 200:
            raise OllamaBackendError(
                f"Ollama HTTP {response.status_code}: {response.text[:200]}"
            )
        data = response.json()
        return (data.get("message") or {}).get("content", "").strip()


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OllamaBackendError(f"model did not return valid JSON: {exc}") from exc
