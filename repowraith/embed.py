from repowraith.config import EMBED_MODEL, OLLAMA_EMBED_URL
from repowraith.errors import OllamaResponseError
from repowraith.models import Chunk, EmbeddedChunk
from repowraith.ollama import post_to_ollama


def embed_text(text: str, model: str = EMBED_MODEL) -> list[float]:
    body = {"model": model, "input": text}
    response_json = post_to_ollama(OLLAMA_EMBED_URL, body, context="embed")

    embeddings = response_json.get("embeddings")

    if not isinstance(embeddings, list) or not embeddings:
        raise OllamaResponseError(
            "Ollama response missing non-empty 'embeddings' list."
        )

    # The api returns a list inside a list. We only want the inner list.
    first_embedding = embeddings[0]

    if not isinstance(first_embedding, list) or not first_embedding:
        raise OllamaResponseError("Ollama response contains invalid embedding vector.")

    if not all(isinstance(value, (int, float)) for value in first_embedding):
        raise OllamaResponseError(
            "Ollama embedding vector contains non-numeric values."
        )

    return first_embedding


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    embedded_chunks = []
    for chunk in chunks:
        vector = embed_text(chunk.text)
        embedded = EmbeddedChunk(chunk=chunk, embedding=vector)
        embedded_chunks.append(embedded)

    return embedded_chunks
