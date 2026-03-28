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
            store[SQLite Index]
        end

        subgraph Query Pipeline
            qembed[Query Embedding]
            retrieve[Hybrid Retrieval]
            prompt[Prompt Builder]
            llmstep[Local LLM Answer]
        end
    end

    repo[(Local Repository)]
    ollama[Ollama API]

    dev --> cli

    cli --> survey
    survey -->|reads files| repo

    survey --> split
    split --> embed
    embed -->|/api/embed| ollama
    embed --> store

    cli --> qembed
    qembed -->|/api/embed| ollama
    qembed --> retrieve
    retrieve -->|loads chunks| store
    retrieve --> prompt
    prompt --> llmstep
    llmstep -->|/api/generate| ollama
    llmstep --> dev
```
