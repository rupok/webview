from webview.chunk import chunk_text, count_tokens


def test_chunk_empty_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_chunk_short_text_returns_single_chunk():
    chunks = chunk_text("Hello world.\n\nThis is fine.", target_tokens=1000)
    assert len(chunks) == 1
    assert "Hello world" in chunks[0].text


def test_chunk_long_text_splits_with_overlap():
    text = "\n\n".join(f"Paragraph {i} " + ("word " * 200) for i in range(10))
    chunks = chunk_text(text, target_tokens=300, overlap_tokens=50)
    assert len(chunks) > 1
    for c in chunks:
        assert c.token_count <= 350


def test_count_tokens_monotonic():
    assert count_tokens("hi") < count_tokens("hi there friend")
