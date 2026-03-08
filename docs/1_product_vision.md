## Overview

RepoWraith is a local code-intelligence tool designed to help developers understand unfamiliar repositories.

It surveys a repository, splits source files into semantic fragments, embeds those fragments using a local embedding model, and enables developers to ask questions about the codebase using semantic search and a local large language model.

The system acts as a semantic archivist, allowing developers to explore and interrogate a codebase without relying on external APIs or cloud services.

## Problem

Developers struggle to understand unfamiliar codebases. Understanding the structure, responsibilities, and behaviour of an unfamiliar repository can be time-consuming and cognitively demanding.

Common challenges include:

- locating where specific functionality is implemented
- understanding relationships between modules
- identifying relevant code across large repositories
- onboarding new developers onto existing systems

## Solution

RepoWraith indexes a repository and allows developers to query it
using semantic search and a local LLM.

The system indexes a repository by:

- surveying files within the repository
- splitting files into overlapping chunks
- generating embedding vectors for each chunk
- storing embeddings in a lightweight local index

When a developer asks a question, RepoWraith embeds the query, retrieves relevant code fragments using similarity search, and constructs a prompt for a local language model to generate an answer with citations to the original source files.

## Target Users

Developers exploring unfamiliar repositories.

The tool is particularly suited to developers who prefer local tooling and privacy-preserving workflows, as it operates entirely on the developer's machine without requiring external APIs.

## Key Features

### Repository Indexing

RepoWraith surveys a repository and builds a searchable semantic index of its contents.

### Semantic Code Search

Developers can locate relevant code fragments using meaning-based search rather than relying solely on keyword matching.

### Natural Language Questions

Developers can ask questions about the codebase in natural language and receive responses grounded in retrieved source code.

### Local-First Architecture

All indexing, embedding, and inference operations run locally, ensuring privacy and eliminating dependency on external services.
