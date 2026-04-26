from repowraith.config import EMBED_BATCH_SIZE, EMBED_MODEL, EMBED_TIMEOUT_SECONDS, OLLAMA_EMBED_URL
from repowraith.errors import OllamaResponseError
from repowraith.models import Chunk, EmbeddedChunk
from repowraith.ollama import post_to_ollama


def _embed_batch(texts: list[str], model: str = EMBED_MODEL) -> list[list[float]]:
    body = {"model": model, "input": texts}
    response_json = post_to_ollama(OLLAMA_EMBED_URL, body, context="embed", timeout=EMBED_TIMEOUT_SECONDS)

    embeddings = response_json.get("embeddings")

    if not isinstance(embeddings, list) or not embeddings:
        raise OllamaResponseError(
            "Ollama response missing non-empty 'embeddings' list."
        )

    for vec in embeddings:
        if not isinstance(vec, list) or not vec:
            raise OllamaResponseError("Ollama response contains invalid embedding vector.")
        if not all(isinstance(v, (int, float)) for v in vec):
            raise OllamaResponseError(
                "Ollama embedding vector contains non-numeric values."
            )

    return embeddings


def embed_text(text: str, model: str = EMBED_MODEL) -> list[float]:
    return _embed_batch([text], model)[0]


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    if not chunks:
        return []

    embedded_chunks = []
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        vectors = _embed_batch([chunk.text for chunk in batch])
        for chunk, vector in zip(batch, vectors):
            embedded_chunks.append(EmbeddedChunk(chunk=chunk, embedding=vector))

    return embedded_chunks
