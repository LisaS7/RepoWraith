# TODO:
# 150 lines per chunk?
# overlap 20-40 lines
# add hashing later?
# Need to store metadata (file path, start & end line, etc) - dataclass?
# Very important to preserve line numbers!


from dataclasses import dataclass
from pathlib import Path

CHUNK_SIZE = 150
OVERLAP = 20


@dataclass
class Chunk:
    file_path: Path
    start_line: int
    end_line: int
    text: str


def split_file(path: Path):
    content = path.read_text(encoding="utf-8").splitlines()
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


def split_repository():
    pass


split_file(Path("repowraith/cli.py"))
