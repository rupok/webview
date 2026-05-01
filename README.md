# WebView

> Let AI view a website.

A small Python library and CLI for fetching web pages, extracting clean
content, and answering questions about them — using **only free or
self-hosted LLM backends**. Zero API keys required to get started.

```bash
pip install webview
webview summarize https://en.wikipedia.org/wiki/Web_browser
```

That's it. No signup, no API key, no model download. The default backend
is a pure-Python extractive summarizer, so WebView does something useful
on a fresh machine before you've configured anything.

When you're ready for real LLM answers, point it at a free backend
(Ollama, Groq free tier, OpenRouter free models, LM Studio, …) by
setting two environment variables. Same code, same CLI, same library.

---

## What it does

```
URL → fetch → extract clean markdown → chunk → cache → (LLM)
```

- **`webview fetch <url>`** — clean markdown of the main content (no nav,
  ads, or footers)
- **`webview summarize <url>`** — concise summary
- **`webview ask <url> "question"`** — Q&A grounded in the page
- **`webview extract <url> --schema schema.json`** — structured JSON
  matching your schema
- **`webview-mcp`** — exposes everything above as MCP tools, so Claude
  Code / Claude Desktop can browse the web through WebView

## Why

The original WebView (2014–2015, archived at
[`archive/eclipse-android`](https://github.com/rupok/webview/tree/archive/eclipse-android))
was an Android template that wrapped a website inside a native app so
**humans** could view a site as an app.

A decade later, the inversion writes itself: **let AI view a website**.
RAG pipelines, agents, research workflows, and your terminal all want
the same thing the old WebView gave humans — a clean, predictable view
of web content. That's what this rewrite delivers.

---

## Install

```bash
pip install webview                    # core
pip install 'webview[playwright]'      # add JS-rendered page support
pip install 'webview[mcp]'             # add MCP server support
```

Python 3.11+. Works offline (after `pip install`) with the default
extractive backend.

---

## Backends

Pick one with `WEBVIEW_BACKEND`. **All of them are free.**

| Backend         | What it is                                  | Setup cost    | When to use |
|-----------------|---------------------------------------------|---------------|-------------|
| `extractive`    | Pure-Python TextRank + BM25 (default)       | None          | Quick starts, offline, deterministic |
| `ollama`        | Local [Ollama](https://ollama.com) daemon   | Local model   | Best privacy & quality, you have a GPU or patience |
| `openai-compat` | Any OpenAI-compatible API                   | Free API key  | Free cloud tiers (Groq, OpenRouter, Together) or local servers (LM Studio, vLLM, llama.cpp) |
| `hf`            | Hugging Face Inference API                  | Free HF token | Hugging Face's free serverless inference |

### Quickest real-LLM setup: Ollama

```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2
export WEBVIEW_BACKEND=ollama
export WEBVIEW_MODEL=llama3.2

webview ask https://example.com "what is this page about?"
```

### Cloud free tier: Groq

```bash
export WEBVIEW_BACKEND=openai-compat
export WEBVIEW_OPENAI_BASE_URL=https://api.groq.com/openai/v1
export WEBVIEW_OPENAI_API_KEY=gsk_...      # free key from console.groq.com
export WEBVIEW_MODEL=llama-3.3-70b-versatile

webview ask https://example.com "what is this page about?"
```

### Cloud free tier: OpenRouter (free models)

```bash
export WEBVIEW_BACKEND=openai-compat
export WEBVIEW_OPENAI_BASE_URL=https://openrouter.ai/api/v1
export WEBVIEW_OPENAI_API_KEY=sk-or-...
export WEBVIEW_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

### Local OpenAI-compatible server: LM Studio / vLLM / llama.cpp

```bash
export WEBVIEW_BACKEND=openai-compat
export WEBVIEW_OPENAI_BASE_URL=http://localhost:1234/v1   # LM Studio default
export WEBVIEW_OPENAI_API_KEY=sk-no-key-required
export WEBVIEW_MODEL=local-model
```

### Hugging Face Inference API

```bash
export WEBVIEW_BACKEND=hf
export WEBVIEW_HF_TOKEN=hf_...     # free at huggingface.co/settings/tokens
export WEBVIEW_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

---

## Library usage

```python
from webview import view

page = view("https://en.wikipedia.org/wiki/Web_browser")

print(page.title)
print(page.summarize(max_sentences=3))
print(page.ask("when was the first web browser released?"))

data = page.extract({
    "type": "object",
    "properties": {
        "title":          {"type": "string"},
        "first_released": {"type": "string"},
        "creators":       {"type": "array"},
    },
})
```

The `Page` object is fully cached — repeated calls reuse the parsed and
chunked content from a local SQLite store.

---

## MCP server

```bash
pip install 'webview[mcp]'
```

Then add to your Claude Code or Claude Desktop config:

```json
{
  "mcpServers": {
    "webview": {"command": "webview-mcp"}
  }
}
```

Now your assistant can call `fetch_page`, `summarize_page`, `ask_page`,
and `extract_page` directly.

---

## Configuration reference

All settings are environment variables prefixed with `WEBVIEW_`.

| Variable                         | Default                              | Notes |
|----------------------------------|--------------------------------------|-------|
| `WEBVIEW_BACKEND`                | `extractive`                         | `extractive` / `ollama` / `openai-compat` / `hf` |
| `WEBVIEW_MODEL`                  | `llama3.2`                           | Model name (backend-specific) |
| `WEBVIEW_OLLAMA_URL`             | `http://localhost:11434`             | Ollama daemon URL |
| `WEBVIEW_OPENAI_BASE_URL`        | `http://localhost:8080/v1`           | OpenAI-compatible server base URL |
| `WEBVIEW_OPENAI_API_KEY`         | `sk-no-key-required`                 | Bearer token |
| `WEBVIEW_HF_TOKEN`               | (empty)                              | Hugging Face token |
| `WEBVIEW_FETCH_TIMEOUT`          | `20.0`                               | Seconds |
| `WEBVIEW_FETCH_MAX_BYTES`        | `5000000`                            | Cap on fetched body size |
| `WEBVIEW_CACHE_DIR`              | OS user cache dir                    | SQLite cache location |
| `WEBVIEW_CACHE_TTL_SECONDS`      | `86400`                              | One day |
| `WEBVIEW_CHUNK_TOKENS`           | `1200`                               | Target tokens per chunk |
| `WEBVIEW_MAX_CONTEXT_TOKENS`     | `8000`                               | Token budget for LLM context |

`webview info` prints the active config.
`webview cache stats|clear|path` manages the cache.

---

## How it works

1. **Fetch** — `httpx` for static pages; optional `playwright` for SPAs.
2. **Extract** — `trafilatura` strips nav/ads/footers and returns markdown.
3. **Chunk** — token-aware paragraph-respecting splitter with overlap.
4. **Cache** — SQLite, keyed by URL, with TTL. Skips fetch + parse on hits.
5. **LLM** — for `ask`/`extract`, BM25 picks the most relevant chunks
   for the query, then the chosen backend answers using only those chunks.

---

## Project history

| Version | Era         | Stack                      | What it did |
|---------|-------------|----------------------------|-------------|
| v1      | 2014–2015   | Eclipse + Java + ADT       | Wrapped a website in an Android WebView app |
| v2      | 2026–       | Python + AI backends       | Lets AI view a website |

v1 lives at branch [`archive/eclipse-android`](https://github.com/rupok/webview/tree/archive/eclipse-android)
and tag `legacy/v1.0-eclipse-2015`. The git history is preserved.

---

## License

GPL-2.0-or-later (carried over from v1).

## Contributing

Issues and PRs welcome. Run tests with:

```bash
pip install -e '.[dev]'
pytest
```
