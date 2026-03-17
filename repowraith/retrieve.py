import json
import math
from dataclasses import dataclass
from pathlib import Path

from repowraith.store import get_connection


@dataclass
class StoredChunk:
    file_path: str
    start_line: int
    end_line: int
    text: str
    embedding: list[float]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def load_chunks(repo_path: Path) -> list[StoredChunk]:
    with get_connection(repo_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_path, start_line, end_line, text, embedding FROM chunks"
        )
        rows = cursor.fetchall()

    chunks = []
    for row in rows:
        stored_chunk = StoredChunk(
            file_path=row["file_path"],
            start_line=row["start_line"],
            end_line=row["end_line"],
            text=row["text"],
            embedding=json.loads(row["embedding"]),
        )
        chunks.append(stored_chunk)

    return chunks
