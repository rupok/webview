"""High-level API: ``view(url)`` returns a ``Page`` object.

Pipeline:
    fetch → extract → chunk → cache → (LLM)

The cache short-circuits the first three steps for repeat requests, which
matters because we run on free/local LLMs where re-tokenizing pages is
relatively expensive.
"""

from __future__ import annotations

from dataclasses import dataclass

from webview import cache, chunk, extract, fetch
from webview.config import Settings, get_settings
from webview.llm import get_llm


@dataclass(slots=True)
class Page:
    """A fetched, extracted, and chunked web page ready for LLM operations."""

    url: str
    final_url: str
    title: str
    author: str | None
    date: str | None
    description: str | None
    sitename: str | None
    markdown: str
    chunks: list[str]
    backend: str

    def summarize(self, *, max_sentences: int = 5) -> str:
        return get_llm().summarize(self.markdown, max_sentences=max_sentences)

    def ask(self, question: str) -> str:
        return get_llm().ask(question, self._context_for_question(question))

    def extract(self, schema: dict) -> dict:
        return get_llm().extract_json(schema, self._context_for_extract())

    def _context_for_question(self, question: str) -> str:
        settings = get_settings()
        return _fit_context(self.chunks, settings.max_context_tokens, prefer=question)

    def _context_for_extract(self) -> str:
        settings = get_settings()
        return _fit_context(self.chunks, settings.max_context_tokens)

    def __str__(self) -> str:
        head = f"# {self.title}\n"
        if self.author:
            head += f"_by {self.author}_\n"
        if self.date:
            head += f"_{self.date}_\n"
        return head + "\n" + self.markdown


def view(
    url: str,
    *,
    render: bool = False,
    refresh: bool = False,
    settings: Settings | None = None,
) -> Page:
    """Fetch, extract, and chunk a URL. Returns a ``Page`` ready for queries.

    On a cache hit (within TTL) the network and parsing steps are skipped.
    Pass ``refresh=True`` to bypass the cache. Pass ``render=True`` to use
    Playwright for JS-heavy pages (requires the ``playwright`` extra).
    """
    settings = settings or get_settings()

    if not refresh:
        cached = cache.get_page(url)
        if cached is not None:
            return _page_from_cache(cached, settings.backend)

    fetched = fetch.fetch(url, render=render)
    extracted = extract.extract(fetched.html, fetched.final_url)

    body = (
        f"# {extracted.title}\n\n{extracted.markdown}"
        if extracted.markdown
        else f"# {extracted.title}"
    )

    chunks = chunk.chunk_text(
        body,
        target_tokens=settings.chunk_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )

    cache.put_page(
        url,
        final_url=fetched.final_url,
        title=extracted.title,
        author=extracted.author,
        date=extracted.date,
        description=extracted.description,
        sitename=extracted.sitename,
        markdown=body,
        etag=fetched.etag,
        chunks=[(c.index, c.text, c.token_count) for c in chunks],
    )

    return Page(
        url=url,
        final_url=fetched.final_url,
        title=extracted.title,
        author=extracted.author,
        date=extracted.date,
        description=extracted.description,
        sitename=extracted.sitename,
        markdown=body,
        chunks=[c.text for c in chunks],
        backend=settings.backend,
    )


def _page_from_cache(cached: dict, backend: str) -> Page:
    return Page(
        url=cached["url"],
        final_url=cached["final_url"],
        title=cached["title"] or cached["url"],
        author=cached["author"],
        date=cached["date"],
        description=cached["description"],
        sitename=cached["sitename"],
        markdown=cached["markdown"],
        chunks=[c["text"] for c in cached["chunks"]],
        backend=backend,
    )


def _fit_context(chunks: list[str], max_tokens: int, *, prefer: str | None = None) -> str:
    """Fit chunks into a token budget, optionally biased toward a query.

    Without ``prefer`` we take leading chunks. With ``prefer`` we BM25-rank
    and take the highest scoring until the budget is exhausted, preserving
    original document order in the output.
    """
    if not chunks:
        return ""

    from webview.chunk import count_tokens

    if prefer is None:
        out: list[str] = []
        used = 0
        for c in chunks:
            tokens = count_tokens(c)
            if used + tokens > max_tokens:
                break
            out.append(c)
            used += tokens
        return "\n\n".join(out)

    import re

    from rank_bm25 import BM25Okapi

    def tokens(s: str) -> list[str]:
        return re.findall(r"\w+", s.lower())

    bm25 = BM25Okapi([tokens(c) for c in chunks])
    scores = bm25.get_scores(tokens(prefer))
    ranked = sorted(enumerate(scores), key=lambda kv: kv[1], reverse=True)

    keep: set[int] = set()
    used = 0
    for idx, _ in ranked:
        c = chunks[idx]
        t = count_tokens(c)
        if used + t > max_tokens:
            continue
        keep.add(idx)
        used += t
        if used >= max_tokens * 0.95:
            break
    return "\n\n".join(chunks[i] for i in sorted(keep))
