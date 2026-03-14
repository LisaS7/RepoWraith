from dataclasses import dataclass

import requests

from repowraith.splitter import Chunk

OLLAMA_API_URL = "http://localhost:11434/api/embed"


@dataclass
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]


def embed_text(text: str, model: str = "embeddinggemma") -> list[float]:
    body = {"model": model, "input": text}

    response = requests.post(OLLAMA_API_URL, json=body)
    response.raise_for_status()

    response_json = response.json()

    embeddings = response_json.get("embeddings")

    if not embeddings:
        raise RuntimeError("Ollama response missing embeddings")

    return embeddings[0]


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    embedded_chunks = []
    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        vector = embed_text(chunk.text)
        embedded = EmbeddedChunk(chunk=chunk, embedding=vector)
        embedded_chunks.append(embedded)

        print(f"Embedded {index}/{total}")

    return embedded_chunks
