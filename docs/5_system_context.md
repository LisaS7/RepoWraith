# RepoLlama — System Context

This diagram shows the external actors and systems that interact with RepoLlama.

RepoLlama operates as a local tool that reads source code from a repository and uses a local language model via Ollama to generate embeddings and answers to developer queries.

```mermaid
flowchart LR

    developer[Developer]
    repo[(Local Repository)]
    ollama[Ollama LLM]
    repollama[[RepoLlama]]

    developer -->|CLI commands| repollama
    repollama -->|Reads files| repo
    repollama -->|Embeddings / responses| ollama

```
