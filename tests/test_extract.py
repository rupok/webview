from webview.extract import extract


def test_extract_returns_title_and_markdown(sample_html: str):
    result = extract(sample_html, "https://example.com/article")
    assert result.title == "Sample Article"
    assert "WebView v2" in result.markdown
    assert "Site nav" not in result.markdown
    assert "Example Corp" not in result.markdown


def test_extract_metadata(sample_html: str):
    result = extract(sample_html, "https://example.com/article")
    assert result.author == "Jane Doe"
    assert result.description and "WebView v2" in result.description
