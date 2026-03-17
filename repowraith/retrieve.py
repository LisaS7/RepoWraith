import json
import math
from pathlib import Path

from repowraith.models import Chunk, EmbeddedChunk, RetrievedChunk
from repowraith.store import get_connection


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def load_chunks(repo_path: Path) -> list[EmbeddedChunk]:
    with get_connection(repo_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_path, start_line, end_line, text, embedding FROM chunks"
        )
        rows = cursor.fetchall()

    chunks = []
    for row in rows:
        chunk = Chunk(
            file_path=Path(row["file_path"]),
            start_line=row["start_line"],
            end_line=row["end_line"],
            text=row["text"],
        )
        embedded_chunk = EmbeddedChunk(
            chunk=chunk,
            embedding=json.loads(row["embedding"]),
        )
        chunks.append(embedded_chunk)

    return chunks


def retrieve_chunks(
    query_embedding: list[float], repo_path: Path, k: int = 5
) -> list[RetrievedChunk]:
    embedded_chunks = load_chunks(repo_path)
    chunks = []
    for embedded_chunk in embedded_chunks:
        score = cosine_similarity(query_embedding, embedded_chunk.embedding)

        retrieved_chunk = RetrievedChunk(embedded_chunk=embedded_chunk, score=score)
        chunks.append(retrieved_chunk)
    chunks.sort(key=lambda chunk: chunk.score, reverse=True)

    return chunks[:k]
