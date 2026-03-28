import requests

from repowraith.config import EMBED_MODEL, OLLAMA_EMBED_URL, REQUEST_TIMEOUT_SECONDS
from repowraith.errors import OllamaConnectionError, OllamaResponseError
from repowraith.models import Chunk, EmbeddedChunk


def embed_text(text: str, model: str = EMBED_MODEL) -> list[float]:
    body = {"model": model, "input": text}

    try:
        response = requests.post(
            OLLAMA_EMBED_URL, json=body, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise OllamaConnectionError(
            f"Timed out waiting for Ollama embeddings response from "
            f"{OLLAMA_EMBED_URL} using model '{model}'."
        ) from exc
    except requests.ConnectionError as exc:
        raise OllamaConnectionError(
            f"Could not connect to Ollama at {OLLAMA_EMBED_URL}. " f"Is Ollama running?"
        ) from exc
    except requests.RequestException as exc:
        raise OllamaConnectionError(f"Ollama embed request failed: {exc}") from exc

    try:
        response_json = response.json()
    except ValueError as exc:
        raise OllamaResponseError(
            "Ollama returned invalid JSON for embeddings request."
        ) from exc

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
    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        vector = embed_text(chunk.text)
        embedded = EmbeddedChunk(chunk=chunk, embedding=vector)
        embedded_chunks.append(embedded)

        print(f"Embedding chunks: {index}/{total}", end="\r")

    print()
    return embedded_chunks
