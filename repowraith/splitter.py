# TODO:
# add hashing later?


from pathlib import Path

from repowraith.config import CHUNK_SIZE, OVERLAP
from repowraith.models import Chunk


def split_file(path: Path) -> list[Chunk]:
    try:
        content = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1").splitlines()
        except Exception:
            return []
    total_lines = len(content)

    start = 0
    chunks = []
    while start < total_lines:
        end = start + CHUNK_SIZE
        chunk_lines = content[start:end]
        chunk = Chunk(
            file_path=path,
            start_line=start + 1,
            end_line=min(end, total_lines),
            text="\n".join(chunk_lines),
        )
        chunks.append(chunk)
        start = end - OVERLAP

    return chunks


def split_repository(files: list[Path]) -> list[Chunk]:
    chunks = []
    for file in files:
        file_chunks = split_file(file)
        chunks.extend(file_chunks)
    return chunks
