from webview.llm.extractive import ExtractiveLLM

ARTICLE = """\
WebView v2 is a Python library for fetching, extracting, and querying web
content with pluggable open-source LLM backends.

It defaults to a zero-LLM extractive backend so it works with no setup.
Contact the author at jane@example.com or visit https://example.com.

The project was published on 2026-04-01 and costs $0 to run. Anyone can
install it from PyPI and start fetching pages immediately.
"""


def test_summarize_returns_non_empty():
    llm = ExtractiveLLM()
    summary = llm.summarize(ARTICLE, max_sentences=2)
    assert summary
    assert len(summary) < len(ARTICLE)


def test_ask_returns_passage_or_not_found():
    llm = ExtractiveLLM()
    answer = llm.ask("What is WebView?", ARTICLE)
    assert "WebView" in answer or "Not found" in answer


def test_ask_empty_context_returns_not_found():
    llm = ExtractiveLLM()
    assert "Not found" in llm.ask("anything?", "")


def test_extract_email_url_date_price():
    llm = ExtractiveLLM()
    schema = {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "website": {"type": "string"},
            "published_date": {"type": "string"},
            "price": {"type": "string"},
            "tags": {"type": "array"},
        },
    }
    out = llm.extract_json(schema, ARTICLE)
    assert out["email"] == "jane@example.com"
    assert out["website"].startswith("https://example.com")
    assert out["published_date"] == "2026-04-01"
    assert "$0" in out["price"]
    assert out["tags"] == []
