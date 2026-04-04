# RepoWraith

_A spectral archivist for your codebase._

RepoWraith haunts your repository, studying its contents and cataloguing its knowledge.

It indexes source files, embeds their meaning, and allows you to ask questions about the code using semantic search and local language models.

No cloud services. No telemetry. Just a quiet intelligence wandering the stacks of your project.

---

## Features

- 📚 Index a repository and build a searchable knowledge archive
- 🔎 Semantic search across source code
- 🧠 Question answering powered by local LLMs via Ollama
- 🕯️ Fully local. Your code never leaves your machine. No external APIs required.

---

## Current Status

Both pipelines are fully implemented:

- **Indexing:** survey → split → embed → store
- **Query:** retrieve → prompt → answer (via local LLM)

---

## Installation

RepoWraith runs entirely locally.

Requirements:

- Python 3.10+
- [Ollama](https://ollama.com/) running locally
- embeddinggemma model installed

Clone the repository and install in editable mode:

```bash
git clone https://github.com/LisaS7/repowraith
cd repowraith
pip install -e .
```

Ensure Ollama is running:

```bash
ollama run embeddinggemma
```

---

## Usage

### Survey a repository

`bash repowraith survey . `

### Survey a repository with file listing

`bash repowraith survey . --verbose `

### Ingest a repository

`bash repowraith ingest . `
This runs the full indexing pipeline

---

## How It Works

RepoWraith builds a local semantic index of a repository.

### Pipeline

```mermaid
flowchart LR
A[Repository] --> B[Survey]
B --> C[Split]
C --> D[Embed]
D --> E[Store]
E --> F[Retrieve]
F --> G[Prompt]
G --> H[Local LLM Answer]
```

1. **Survey**
   Discover repository files while ignoring irrelevant paths such as `.git`, `.venv`, `__pycache__`, etc.

2. **Split**
   Break files into overlapping chunks sized for embedding and retrieval.

3. **Embed**
   Send chunk text to Ollama's local embedding API.

4. **Store**
   Persist chunks and embeddings in a local SQLite database.

---

## Local Storage

RepoWraith stores its index locally inside the target repository:
`text &lt;repo_root&gt;/.repowraith/index.db `

Embeddings are stored as JSON-encoded vectors in SQLite.

---

## Roadmap

### Completed

- CLI interface
- Repository survey
- Chunking pipeline
- Ollama embeddings
- SQLite storage
- Hybrid semantic + BM25 retrieval
- Prompt assembly
- Local LLM question answering (`repowraith ask`)

### Planned

- `repowraith status`
- `repowraith reindex`
- `repowraith inspect`
