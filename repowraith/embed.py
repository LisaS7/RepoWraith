import requests

from repowraith.config import EMBED_MODEL, OLLAMA_EMBED_URL
from repowraith.models import Chunk, EmbeddedChunk


def embed_text(text: str, model: str = EMBED_MODEL) -> list[float]:
    body = {"model": model, "input": text}

    response = requests.post(OLLAMA_EMBED_URL, json=body)
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

        print(f"Embedding chunks: {index}/{total}", end="\r")

    print()
    return embedded_chunks
