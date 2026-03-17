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


@dataclass
class RetrievedChunk:
    embedded_chunk: EmbeddedChunk
    score: float
