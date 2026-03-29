import datetime
import json
import sqlite3
from pathlib import Path

from repowraith.models import Chunk, EmbeddedChunk
from repowraith.schema import (
    CREATE_CHUNKS_REPO_INDEX,
    CREATE_CHUNKS_TABLE,
    CREATE_REPOSITORIES_TABLE,
)


def get_db_path(repo_path: Path) -> Path:
    return repo_path / ".repowraith" / "index.db"


def get_repo_id(conn: sqlite3.Connection, repo_path: Path) -> int:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM repositories WHERE root_path = ?",
        (str(repo_path.resolve()),),
    )
    repo_row = cursor.fetchone()

    if repo_row is None:
        raise ValueError(f"Repository not found in index: {repo_path}")

    return repo_row["id"]


def get_connection(repo_path: Path) -> sqlite3.Connection:
    db_path = get_db_path(repo_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute(CREATE_REPOSITORIES_TABLE)
    cursor.execute(CREATE_CHUNKS_TABLE)
    cursor.execute(CREATE_CHUNKS_REPO_INDEX)


def upsert_repository(conn: sqlite3.Connection, repo_path: Path) -> int:
    root_path = str(repo_path.resolve())
    indexed_at = datetime.datetime.now().isoformat()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO repositories (root_path, indexed_at)
        VALUES (?, ?)
        ON CONFLICT(root_path) DO UPDATE SET
        indexed_at = excluded.indexed_at
        """,
        (root_path, indexed_at),
    )

    cursor.execute(
        "SELECT id FROM repositories WHERE root_path = ?",
        (root_path,),
    )

    row = cursor.fetchone()

    if row is None:
        raise RuntimeError("Failed to fetch repository id after upsert")

    return row["id"]


def delete_chunks_for_repo(conn: sqlite3.Connection, repo_id: int) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM chunks WHERE repo_id = ?",
        (repo_id,),
    )


def insert_chunks(
    conn: sqlite3.Connection,
    repo_id: int,
    repo_path: Path,
    embedded_chunks: list[EmbeddedChunk],
) -> None:

    if not embedded_chunks:
        return

    rows = []
    for embedded_chunk in embedded_chunks:
        chunk = embedded_chunk.chunk
        relative_file_path = chunk.file_path.relative_to(repo_path).as_posix()
        embedding_json = json.dumps(embedded_chunk.embedding)

        row = (
            repo_id,
            relative_file_path,
            chunk.start_line,
            chunk.end_line,
            chunk.text,
            embedding_json,
        )
        rows.append(row)

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO chunks (repo_id, file_path, start_line, end_line, text, embedding) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )


def load_chunks(repo_path: Path) -> list[EmbeddedChunk]:
    with get_connection(repo_path) as conn:
        repo_id = get_repo_id(conn, repo_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_path, start_line, end_line, text, embedding FROM chunks WHERE repo_id = ?",
            (repo_id,),
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


def index_repository(repo_path: Path, embedded_chunks: list[EmbeddedChunk]) -> None:
    with get_connection(repo_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, repo_path)
        delete_chunks_for_repo(conn, repo_id)
        insert_chunks(conn, repo_id, repo_path, embedded_chunks)
