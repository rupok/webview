"""Token-aware chunking for LLM context windows.

Tries tiktoken's cl100k_base first (a reasonable proxy across modern
tokenizers — off by 10-20% for non-OpenAI models, which is fine for
budgeting). Falls back to a word-count heuristic (~1.3 tokens/word) when
tiktoken can't load its BPE file (offline machines, sandboxed CI).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol


@dataclass(slots=True)
class Chunk:
    index: int
    text: str
    token_count: int


class _Encoder(Protocol):
    def encode(self, text: str) -> list[int]: ...
    def decode(self, tokens: list[int]) -> str: ...


class _WordEncoder:
    """Fallback encoder: each token approximates one whitespace-separated word x 1.3."""

    _SPLIT = re.compile(r"(\s+)")

    def encode(self, text: str) -> list[int]:
        words = [w for w in self._SPLIT.split(text) if w]
        return list(range(int(len(words) * 1.3) or len(words)))

    def decode(self, tokens: list[int]) -> str:
        return ""


@lru_cache(maxsize=1)
def _encoder() -> _Encoder:
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return _WordEncoder()


def count_tokens(text: str) -> int:
    return len(_encoder().encode(text))


def chunk_text(text: str, *, target_tokens: int = 1200, overlap_tokens: int = 100) -> list[Chunk]:
    """Split text into overlapping chunks of roughly ``target_tokens`` each.

    Splits on paragraph boundaries when possible; falls back to character-window
    splitting for paragraphs larger than the target.
    """
    if not text.strip():
        return []

    enc = _encoder()
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_tokens = 0

    def flush() -> None:
        nonlocal buffer, buffer_tokens
        if not buffer:
            return
        chunk_str = "\n\n".join(buffer).strip()
        if chunk_str:
            chunks.append(Chunk(index=len(chunks), text=chunk_str, token_count=buffer_tokens))
        buffer = []
        buffer_tokens = 0

    for para in paragraphs:
        para_tokens = len(enc.encode(para))

        if para_tokens > target_tokens:
            flush()
            for piece in _split_oversized(para, target_tokens, overlap_tokens):
                chunks.append(
                    Chunk(
                        index=len(chunks),
                        text=piece,
                        token_count=len(enc.encode(piece)),
                    )
                )
            continue

        if buffer_tokens + para_tokens > target_tokens and buffer:
            flush()
        buffer.append(para)
        buffer_tokens += para_tokens

    flush()
    return chunks


def _split_oversized(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    """Split a too-large paragraph into character windows sized to the budget.

    Approximation is fine here: this only fires for outlier paragraphs.
    """
    enc = _encoder()
    total_tokens = len(enc.encode(text)) or 1
    chars_per_token = max(1, len(text) // total_tokens)

    window_chars = target_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token
    step = max(1, window_chars - overlap_chars)

    out: list[str] = []
    for start in range(0, len(text), step):
        piece = text[start : start + window_chars]
        if piece.strip():
            out.append(piece)
    return out
