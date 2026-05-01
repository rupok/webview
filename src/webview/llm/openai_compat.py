"""OpenAI-compatible backend.

One adapter, many free providers:

  - **Groq** (free tier)              base=https://api.groq.com/openai/v1
  - **OpenRouter** (free models)      base=https://openrouter.ai/api/v1
  - **Together** (free tier)          base=https://api.together.xyz/v1
  - **LM Studio** (local)             base=http://localhost:1234/v1
  - **vLLM / llama.cpp server**       base=http://localhost:8080/v1

All speak the same /chat/completions API. Set:
    WEBVIEW_BACKEND=openai-compat
    WEBVIEW_OPENAI_BASE_URL=...
    WEBVIEW_OPENAI_API_KEY=...   (any value for local servers)
    WEBVIEW_MODEL=...
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


class OpenAICompatError(RuntimeError):
    pass


class OpenAICompatLLM:
    name = "openai-compat"

    def __init__(self, base_url: str, api_key: str, model: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def summarize(self, text: str, *, max_sentences: int = 5) -> str:
        return self._chat(SUMMARIZE_SYSTEM, summarize_user(text, max_sentences))

    def ask(self, question: str, context: str) -> str:
        return self._chat(ASK_SYSTEM, ask_user(question, context))

    def extract_json(self, schema: dict, context: str) -> dict:
        raw = self._chat(
            EXTRACT_SYSTEM,
            extract_user(schema, context),
            response_format={"type": "json_object"},
        )
        return _parse_json(raw)

    def _chat(
        self,
        system: str,
        user: str,
        *,
        response_format: dict | None = None,
    ) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise OpenAICompatError(
                f"could not reach {self.base_url}: {exc}"
            ) from exc

        if response.status_code != 200:
            raise OpenAICompatError(
                f"HTTP {response.status_code} from {self.base_url}: {response.text[:200]}"
            )
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            raise OpenAICompatError(f"unexpected response shape: {data}") from exc


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
        raise OpenAICompatError(f"model did not return valid JSON: {exc}") from exc
