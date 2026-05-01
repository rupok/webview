"""HTML → clean markdown extraction via trafilatura.

trafilatura is best-in-class OSS for this — it discards nav/footer/ads,
keeps body content, and emits markdown with preserved structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import trafilatura
from trafilatura.metadata import extract_metadata


@dataclass(slots=True)
class ExtractedContent:
    title: str
    author: str | None
    date: str | None
    description: str | None
    sitename: str | None
    markdown: str
    links: list[str] = field(default_factory=list)


def extract(html: str, url: str) -> ExtractedContent:
    """Extract main-article content from raw HTML."""
    markdown = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_links=True,
        include_images=True,
        include_tables=True,
        favor_recall=True,
    ) or ""

    meta = extract_metadata(html, default_url=url)

    title = (meta.title if meta else None) or _fallback_title(html) or url
    author = meta.author if meta else None
    date = meta.date if meta else None
    description = meta.description if meta else None
    sitename = meta.sitename if meta else None

    links: list[str] = []
    if meta and getattr(meta, "url", None):
        links.append(meta.url)

    return ExtractedContent(
        title=title,
        author=author,
        date=date,
        description=description,
        sitename=sitename,
        markdown=markdown.strip(),
        links=links,
    )


def _fallback_title(html: str) -> str | None:
    lower = html.lower()
    start = lower.find("<title")
    if start < 0:
        return None
    gt = lower.find(">", start)
    end = lower.find("</title>", gt)
    if gt < 0 or end < 0:
        return None
    return html[gt + 1 : end].strip() or None
