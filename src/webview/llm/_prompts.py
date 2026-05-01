"""Shared prompt templates for backends that hit a real LLM."""

from __future__ import annotations

import json

SUMMARIZE_SYSTEM = (
    "You produce concise, faithful summaries of web articles. "
    "Stick to information present in the provided text. "
    "Do not invent facts. Output only the summary, no preamble."
)


def summarize_user(text: str, max_sentences: int) -> str:
    return (
        f"Summarize the following article in at most {max_sentences} sentences. "
        f"Capture the main thesis and key supporting points.\n\n---\n{text}\n---"
    )


ASK_SYSTEM = (
    "You answer questions strictly from the supplied web page content. "
    "If the answer is not in the content, reply: \"Not found in the page.\" "
    "Quote short snippets when helpful. Be brief."
)


def ask_user(question: str, context: str) -> str:
    return (
        f"PAGE CONTENT:\n---\n{context}\n---\n\nQUESTION: {question}\n\nANSWER:"
    )


EXTRACT_SYSTEM = (
    "You extract structured data from web pages. "
    "Return a single JSON object that matches the requested schema exactly. "
    "Use null for fields you cannot determine. Output JSON only — no prose, no fences."
)


def extract_user(schema: dict, context: str) -> str:
    return (
        f"SCHEMA:\n{json.dumps(schema, indent=2)}\n\n"
        f"PAGE CONTENT:\n---\n{context}\n---\n\n"
        "Return JSON matching the schema:"
    )
