import sqlite3
from pathlib import Path

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
