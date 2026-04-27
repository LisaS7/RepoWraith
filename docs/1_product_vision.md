# Product Vision: RepoLlama

## Overview
RepoLlama is a local-first developer tool that acts as a local archivist for your codebase. It enables developers to query and understand unfamiliar repositories quickly, without relying on external services or uploading sensitive code.


## Problem Statement

Developers struggle to understand unfamiliar codebases. Understanding the structure, responsibilities, and behaviour of an unfamiliar repository can be time-consuming and cognitively demanding.

Common challenges include:

- locating where specific functionality is implemented
- understanding relationships between modules
- identifying relevant code across large repositories
- onboarding new developers onto existing systems

## Solution
RepoLlama builds a local index of a repository and allows users to ask natural language questions about the code.

It works by:

- Scanning and chunking source files
- Generating embedding vectors
- Storing data locally in a lightweight database
- Retrieving relevant code using hybrid search (semantic + lexical/BM25)
- Generating answers using a local LLM

## Key Features
- Fully local processing (no external data sharing)
- Hybrid retrieval for improved relevance:
  - Semantic similarity (embeddings)
  - Lexical relevance (BM25 scoring)
- Lightweight and fast indexing
- Clear traceability (file paths + line ranges)
- Simple CLI interface

## Target Users
- Developers exploring unfamiliar codebases
- Engineers onboarding onto new projects
- Privacy-conscious teams working with sensitive code

## Value Proposition
RepoLlama provides fast, private, and accurate code understanding by combining modern LLM capabilities with traditional information retrieval techniques.

## Future Vision
- Structure-aware chunking (AST-based)
- Ranking improvements and tuning
- Lightweight UI for browsing results
