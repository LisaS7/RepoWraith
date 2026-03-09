# RepoWraith Architecture Overview

This diagram illustrates the high-level architecture of RepoWraith,
showing the indexing pipeline used to build the repository index
and the query pipeline used to answer developer questions.

```mermaid
flowchart LR

    dev[Developer]

    subgraph RepoWraith
        cli[CLI Interface]

        subgraph Indexing Pipeline
            survey[Repository Survey]
            split[Chunk Splitter]
            embed[Embedding Generator]
            store[(SQLite Vector Store)]
        end

        subgraph Query Pipeline
            qembed[Query Embedding]
            retrieve[Similarity Retrieval]
            prompt[Prompt Assembly]
        end
    end

    repo[(Local Repository)]
    ollama[Ollama LLM / Embeddings]

    dev --> cli

    cli --> survey
    survey --> repo

    survey --> split
    split --> embed
    embed --> ollama
    embed --> store

    cli --> qembed
    qembed --> ollama
    qembed --> retrieve
    retrieve --> store
    retrieve --> prompt
    prompt --> ollama
    prompt --> dev
```
