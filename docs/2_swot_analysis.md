## SWOT

## Internal Factors

### Strengths

> - Local-first architecture (no external APIs required)
> - Simple, portable stack (Python + SQLite)
> - Deterministic chunking with line citations
> - Modular pipeline design (survey → split → embed → retrieve)

### Weaknesses

> - Limited scalability for large repositories
> - Chunking ignores code structure (functions/classes)
> - No incremental indexing yet
> - CLI-only interface may limit accessibility

---

## External Factors

### Opportunities

> - Rising interest in local AI tooling
> - Potential IDE integrations (e.g. VSCode extension)
> - Codebase onboarding and developer documentation tools
> - Educational tooling for exploring repositories

### Threats

> - Rapid evolution of AI developer tooling
> - Large IDE platforms integrating semantic search
> - Vector database tools offering scalable alternatives
> - Increasing LLM context windows reducing need for chunking

---

## Strategic Interpretation

The analysis suggests RepoWraith should prioritise:

- Maintaining a lightweight, local-first architecture
- Improving retrieval accuracy through smarter chunking
- Positioning the tool as a transparent and hackable code-intelligence pipeline for developers exploring local AI tooling
