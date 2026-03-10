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
    return response_json["embeddings"][0]


def embed_chunks(chunks: list[Chunk]):
    for chunk in chunks:
        pass
