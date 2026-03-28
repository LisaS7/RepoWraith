```mermaid
flowchart LR

    developer[Developer]

    subgraph system[RepoWraith]
        survey(Survey repository)
        ingest(Ingest repository)
        ask(Ask question about codebase)

    end

    developer --> survey
    developer --> ingest
    developer --> ask

```
