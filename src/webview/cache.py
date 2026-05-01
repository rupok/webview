"""SQLite-backed page cache.

Avoids re-fetching and re-extracting the same URL — the expensive operations
in this stack are network IO and HTML parsing, not LLM calls (which are local
or free-tier in this project).
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from webview.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    url           TEXT PRIMARY KEY,
    final_url     TEXT NOT NULL,
    title         TEXT,
    author        TEXT,
    date          TEXT,
    description   TEXT,
    sitename      TEXT,
    markdown      TEXT NOT NULL,
    etag          TEXT,
    fetched_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    url           TEXT NOT NULL,
    idx           INTEGER NOT NULL,
    text          TEXT NOT NULL,
    token_count   INTEGER NOT NULL,
    PRIMARY KEY (url, idx)
);
"""


@contextmanager
def _connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    db_path = path or settings.cache_db_path()
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_page(url: str) -> dict | None:
    settings = get_settings()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM pages WHERE url = ?", (url,)).fetchone()
        if row is None:
            return None
        if time.time() - row["fetched_at"] > settings.cache_ttl_seconds:
            return None
        chunks = conn.execute(
            "SELECT idx, text, token_count FROM chunks WHERE url = ? ORDER BY idx", (url,)
        ).fetchall()
    return {
        "url": row["url"],
        "final_url": row["final_url"],
        "title": row["title"],
        "author": row["author"],
        "date": row["date"],
        "description": row["description"],
        "sitename": row["sitename"],
        "markdown": row["markdown"],
        "etag": row["etag"],
        "fetched_at": row["fetched_at"],
        "chunks": [dict(c) for c in chunks],
    }


def put_page(
    url: str,
    *,
    final_url: str,
    title: str,
    author: str | None,
    date: str | None,
    description: str | None,
    sitename: str | None,
    markdown: str,
    etag: str | None,
    chunks: list[tuple[int, str, int]],
) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO pages "
            "(url, final_url, title, author, date, description, sitename, markdown, etag, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (url, final_url, title, author, date, description, sitename, markdown, etag, time.time()),
        )
        conn.execute("DELETE FROM chunks WHERE url = ?", (url,))
        conn.executemany(
            "INSERT INTO chunks (url, idx, text, token_count) VALUES (?, ?, ?, ?)",
            [(url, idx, text, tokens) for idx, text, tokens in chunks],
        )


def clear() -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM pages")


def stats() -> dict:
    with _connect() as conn:
        page_count = conn.execute("SELECT COUNT(*) AS n FROM pages").fetchone()["n"]
        chunk_count = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
    return {"pages": page_count, "chunks": chunk_count, "db": str(get_settings().cache_db_path())}


def export_json(path: Path) -> int:
    with _connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM pages").fetchall()]
    path.write_text(json.dumps(rows, indent=2))
    return len(rows)
