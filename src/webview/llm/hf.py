"""Hugging Face Inference API backend (free tier).

Uses the chat-completions-style router endpoint. A token is required for
the free tier (sign up at https://huggingface.co/settings/tokens — read
access is enough for inference).

    WEBVIEW_BACKEND=hf
    WEBVIEW_HF_TOKEN=hf_xxx
    WEBVIEW_MODEL=meta-llama/Llama-3.2-3B-Instruct
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

_BASE = "https://router.huggingface.co/v1"


class HuggingFaceBackendError(RuntimeError):
    pass


class HuggingFaceLLM:
    name = "hf"

    def __init__(self, token: str, model: str, *, timeout: float = 120.0) -> None:
        if not token:
            raise HuggingFaceBackendError(
                "WEBVIEW_HF_TOKEN is empty. Get a free token at "
                "https://huggingface.co/settings/tokens"
            )
        self.token = token
        self.model = model
        self.timeout = timeout

    def summarize(self, text: str, *, max_sentences: int = 5) -> str:
        return self._chat(SUMMARIZE_SYSTEM, summarize_user(text, max_sentences))

    def ask(self, question: str, context: str) -> str:
        return self._chat(ASK_SYSTEM, ask_user(question, context))

    def extract_json(self, schema: dict, context: str) -> dict:
        raw = self._chat(EXTRACT_SYSTEM, extract_user(schema, context))
        return _parse_json(raw)

    def _chat(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{_BASE}/chat/completions",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise HuggingFaceBackendError(f"HF inference network error: {exc}") from exc

        if response.status_code != 200:
            raise HuggingFaceBackendError(
                f"HF inference HTTP {response.status_code}: {response.text[:200]}"
            )
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise HuggingFaceBackendError(f"unexpected HF response: {data}") from exc


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
        raise HuggingFaceBackendError(f"model did not return valid JSON: {exc}") from exc
