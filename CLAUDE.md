# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in development mode
pip install -e .

# Run all tests
pytest

# Run a single test file
pytest tests/test_retrieve.py

# Run a single test function
pytest tests/test_retrieve.py::test_function_name

# Run the CLI
repowraith survey <path>
repowraith ingest <path>
repowraith ask <path> "<question>"
```

## Architecture

RepoWraith indexes local codebases and answers questions about them using local embeddings (Ollama) and a local LLM — no cloud services.

### Two pipelines

**Indexing** (`repowraith ingest <path>`):
`survey.py` → `splitter.py` → `embed.py` → `store.py`

1. **Survey** — discover files, skip non-code dirs/extensions
2. **Split** — break files into overlapping line chunks (150 lines, 20-line overlap)
3. **Embed** — call Ollama embedding API (`embeddinggemma` model)
4. **Store** — persist chunks + embeddings to SQLite at `<repo>/.repowraith/index.db`

**Query** (`repowraith ask <path> "<question>"`):
`retrieve.py` → `prompt.py` → `llm.py`

1. **Retrieve** — embed the question, then score stored chunks using hybrid retrieval: cosine similarity + BM25 lexical scoring (50/50 weight by default), return top-K=5
2. **Prompt** — format retrieved chunks into a structured prompt using `prompt_template.txt`
3. **LLM** — send prompt to Ollama (`llama3` model) and stream the answer

### Key modules

| File | Role |
|------|------|
| `cli.py` | Entry point, argument parsing, `cmd_survey/ingest/ask` |
| `config.py` | All tunable constants (chunk size, model names, Ollama URL, BM25 params) |
| `models.py` | Data classes: `Chunk`, `EmbeddedChunk`, `RetrievedChunk` |
| `errors.py` | Exception hierarchy: `RepoWraithError` → `OllamaError` → `OllamaConnectionError`/`OllamaResponseError` |
| `schema.py` | SQLite table DDL (`repositories`, `chunks`) |
| `store.py` | All DB reads/writes |
| `retrieve.py` | Hybrid retrieval logic (semantic + BM25 scoring) |

### External dependency

All AI inference goes through **Ollama** at `http://localhost:11434`. If Ollama is not running, `OllamaConnectionError` is raised. The embedding model and LLM are configured in `config.py`.

## Development guidelines

- Prefer small, incremental changes over large rewrites
- Always explain reasoning before suggesting code changes
- Do not assume functionality exists unless it is present in the codebase
- Keep solutions simple and consistent with existing patterns
- Avoid introducing unnecessary abstractions or complexity

## Debugging approach

- Start by identifying where in the pipeline the issue occurs (survey, split, embed, store, retrieve, prompt, llm)
- Use existing debug output before adding new logging
- When investigating retrieval issues, consider both semantic and lexical scores

## Important concepts

- A `Chunk` represents a slice of a file with line numbers
- `EmbeddedChunk` adds a vector embedding
- `RetrievedChunk` adds a relevance score
- Line numbers are important for traceability and must be preserved

## Constraints

- This is a fully local tool — no external APIs beyond Ollama
- Ollama must be running for embedding and LLM calls
- SQLite is the only persistence layer
