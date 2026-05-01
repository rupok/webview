from webview import cache


def test_put_then_get_roundtrip():
    cache.put_page(
        "https://example.com/x",
        final_url="https://example.com/x",
        title="Title",
        author="A",
        date="2026-01-01",
        description="d",
        sitename="Example",
        markdown="# body",
        etag=None,
        chunks=[(0, "first chunk", 2), (1, "second chunk", 2)],
    )
    got = cache.get_page("https://example.com/x")
    assert got is not None
    assert got["title"] == "Title"
    assert len(got["chunks"]) == 2
    assert got["chunks"][0]["text"] == "first chunk"


def test_clear_removes_pages():
    cache.put_page(
        "https://example.com/y",
        final_url="https://example.com/y",
        title="t",
        author=None,
        date=None,
        description=None,
        sitename=None,
        markdown="b",
        etag=None,
        chunks=[(0, "c", 1)],
    )
    assert cache.get_page("https://example.com/y") is not None
    cache.clear()
    assert cache.get_page("https://example.com/y") is None


def test_stats_reports_counts():
    cache.clear()
    cache.put_page(
        "https://example.com/z",
        final_url="https://example.com/z",
        title="t",
        author=None,
        date=None,
        description=None,
        sitename=None,
        markdown="b",
        etag=None,
        chunks=[(0, "c", 1), (1, "d", 1)],
    )
    s = cache.stats()
    assert s["pages"] == 1
    assert s["chunks"] == 2
