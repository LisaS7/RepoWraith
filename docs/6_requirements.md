# Requirements: RepoLlama

## Functional Requirements

FR1: The system shall allow users to index a local repository
FR2: The system shall allow users to query the repository using natural language
FR3: The system shall retrieve relevant code chunks using hybrid ranking

## Non-Functional Requirements

NFR1: All processing must occur locally (no external data transmission)
NFR2: Queries should return results within 3 seconds for small repos
NFR3: System must handle repositories up to X files

## Acceptance Criteria

FR2:
- Given a user has indexed a repo
- When they run `repollama ask`
- Then the system returns an answer with relevant code context
