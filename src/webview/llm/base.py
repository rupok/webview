"""LLM protocol that every backend implements.

Kept deliberately small — three operations is enough to power summarize,
ask, and structured-extract for the v2 surface area. Adding a new backend
means implementing this Protocol; nothing else in the codebase needs to
change.
"""

from __future__ import annotations

from typing import Protocol


class LLM(Protocol):
    """Minimum surface every backend must provide."""

    name: str

    def summarize(self, text: str, *, max_sentences: int = 5) -> str:
        """Return a concise summary of ``text``."""
        ...

    def ask(self, question: str, context: str) -> str:
        """Answer ``question`` using ``context`` as the only source of truth."""
        ...

    def extract_json(self, schema: dict, context: str) -> dict:
        """Return data conforming to ``schema``, drawn from ``context``."""
        ...
