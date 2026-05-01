"""Zero-LLM backend.

Lets WebView do something useful on a fresh laptop with no model and no
network beyond the page fetch itself.

  - summarize: TextRank via sumy (sentence ranking by graph centrality)
  - ask:       BM25 ranking over chunks, returns the best-matching passages
  - extract:   regex/heuristic extraction for common scalar fields, null
               for anything it cannot confidently determine
"""

from __future__ import annotations

import contextlib
import json
import re
from typing import Any

import nltk
from rank_bm25 import BM25Okapi
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.text_rank import TextRankSummarizer

_NLTK_READY = False


def _ensure_nltk() -> None:
    global _NLTK_READY
    if _NLTK_READY:
        return
    for pkg in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{pkg}")
        except LookupError:
            with contextlib.suppress(Exception):
                nltk.download(pkg, quiet=True)
    _NLTK_READY = True


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class ExtractiveLLM:
    """No-LLM backend. Fast, deterministic, surprisingly useful for many pages."""

    name = "extractive"

    def summarize(self, text: str, *, max_sentences: int = 5) -> str:
        if not text.strip():
            return ""
        _ensure_nltk()
        try:
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            summarizer = TextRankSummarizer(Stemmer("english"))
            sentences = summarizer(parser.document, max_sentences)
            joined = " ".join(str(s) for s in sentences).strip()
            if joined:
                return joined
        except Exception:
            pass
        return _naive_summary(text, max_sentences)

    def ask(self, question: str, context: str) -> str:
        paragraphs = [p.strip() for p in context.split("\n\n") if p.strip()]
        if not paragraphs:
            return "Not found in the page."

        tokenized = [_tokenize(p) for p in paragraphs]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(_tokenize(question))
        ranked = sorted(
            zip(scores, paragraphs, strict=True), key=lambda kv: kv[0], reverse=True
        )

        top = [p for score, p in ranked[:3] if score > 0]
        if not top:
            return "Not found in the page."

        prefix = "(extractive backend — no LLM; showing best-matching passages)\n\n"
        return prefix + "\n\n---\n\n".join(top)

    def extract_json(self, schema: dict, context: str) -> dict:
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        result: dict[str, Any] = {}
        for field, spec in properties.items():
            result[field] = _heuristic_field(field, spec, context)
        return result


def _naive_summary(text: str, max_sentences: int) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:max_sentences])


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL_RE = re.compile(r"https?://[^\s)\]]+")
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_PRICE_RE = re.compile(r"\$\s?\d+(?:[.,]\d+)?")


def _heuristic_field(field: str, spec: dict, context: str) -> Any:
    name = field.lower()
    field_type = (spec or {}).get("type", "string") if isinstance(spec, dict) else "string"

    if "email" in name:
        match = _EMAIL_RE.search(context)
        return match.group(0) if match else None
    if any(k in name for k in ("url", "link", "website")):
        match = _URL_RE.search(context)
        return match.group(0) if match else None
    if "date" in name or "published" in name:
        match = _DATE_RE.search(context)
        return match.group(0) if match else None
    if "price" in name or "cost" in name:
        match = _PRICE_RE.search(context)
        return match.group(0) if match else None
    if "title" in name or "headline" in name:
        first_line = next((line for line in context.splitlines() if line.strip()), "")
        return first_line.lstrip("# ").strip() or None

    if field_type == "array":
        return []
    if field_type in ("integer", "number"):
        return None
    if field_type == "boolean":
        return None
    return None


def __getattr__(name: str):
    if name == "json":
        return json
    raise AttributeError(name)
