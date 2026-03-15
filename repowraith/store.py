import datetime
import sqlite3
from pathlib import Path

from repowraith.embed import EmbeddedChunk
from repowraith.schema import (
    CREATE_CHUNKS_REPO_INDEX,
    CREATE_CHUNKS_TABLE,
    CREATE_REPOSITORIES_TABLE,
)


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


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

    return row[0]


def delete_chunks_for_repo(conn: sqlite3.Connection, repo_id: int):
    pass


def insert_chunks():
    pass


def index_repository(repo_path: Path, embedded_chunks: list[EmbeddedChunk]) -> None:
    db_path = repo_path / ".repowraith" / "index.db"

    with get_connection(db_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, repo_path)
