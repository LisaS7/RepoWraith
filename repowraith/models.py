from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    file_path: Path
    start_line: int
    end_line: int
    text: str


@dataclass
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]
    file_hash: str = ""


@dataclass
class RetrievedChunk:
    embedded_chunk: EmbeddedChunk
    score: float
    semantic_score: float = 0.0
    lexical_score: float = 0.0
    file_score: float = 0.0
    test_penalized: bool = False
    rerank_score: float | None = None

    @property
    def chunk(self) -> Chunk:
        return self.embedded_chunk.chunk
