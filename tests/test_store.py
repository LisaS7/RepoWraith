import json
import sqlite3
import time

from repowraith.embed import EmbeddedChunk
from repowraith.splitter import Chunk
from repowraith.store import (
    delete_chunks_for_repo,
    get_connection,
    init_db,
    insert_chunks,
    upsert_repository,
)


def test_get_connection(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"
    with get_connection(db_path) as conn:
        assert (tmp_path / ".repowraith").exists()
        assert db_path.exists()
        assert isinstance(conn, sqlite3.Connection)


def test_init_db(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    with get_connection(db_path) as conn:
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

    assert "repositories" in tables
    assert "chunks" in tables
    assert "idx_chunks_repo_id" in indexes


def test_upsert_repository_inserts_row(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    with get_connection(db_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        cursor = conn.cursor()
        cursor.execute("SELECT id, root_path, indexed_at FROM repositories")
        rows = cursor.fetchall()

        assert len(rows) == 1

        row = rows[0]
        assert row[0] == repo_id
        assert row[1] == str(tmp_path.resolve())
        assert row[2] is not None


def test_upsert_repository_does_not_duplicate(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    with get_connection(db_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        cursor = conn.cursor()

        repo_id_2 = upsert_repository(conn, tmp_path)
        cursor.execute("SELECT id FROM repositories")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert repo_id_2 == repo_id
        assert rows[0][0] == repo_id


def test_upsert_repository_updates_indexed_at(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    with get_connection(db_path) as conn:
        init_db(conn)

        upsert_repository(conn, tmp_path)

        cursor = conn.cursor()
        cursor.execute("SELECT indexed_at FROM repositories")
        first_indexed_at = cursor.fetchone()[0]

        time.sleep(0.01)

        upsert_repository(conn, tmp_path)

        cursor.execute("SELECT indexed_at FROM repositories")
        second_indexed_at = cursor.fetchone()[0]

        assert second_indexed_at != first_indexed_at


def test_delete_chunks_for_repo(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    with get_connection(db_path) as conn:
        init_db(conn)

        repo_id_1 = upsert_repository(conn, tmp_path)
        repo_id_2 = upsert_repository(conn, tmp_path / "other_repo")

        cursor = conn.cursor()

        cursor.executemany(
            """
            INSERT INTO chunks (repo_id, file_path, start_line, end_line, text, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (repo_id_1, "file1.py", 1, 10, "chunk one", "[0.1, 0.2]"),
                (repo_id_1, "file2.py", 11, 20, "chunk two", "[0.3, 0.4]"),
                (repo_id_2, "other.py", 1, 5, "other repo chunk", "[0.5, 0.6]"),
            ],
        )

        # Check chunks have inserted
        cursor.execute("SELECT COUNT(*) FROM chunks")
        assert cursor.fetchone()[0] == 3

        delete_chunks_for_repo(conn, repo_id_1)

        # Check chunks have deleted
        cursor.execute("SELECT COUNT(*) FROM chunks")
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT repo_id, file_path FROM chunks")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == repo_id_2
        assert rows[0][1] == "other.py"


def test_insert_chunks_single_row(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    chunk = Chunk(
        file_path=tmp_path / "folder" / "test.py",
        start_line=1,
        end_line=3,
        text="print('hello')",
    )

    embedded_chunk = EmbeddedChunk(
        chunk=chunk,
        embedding=[0.1, 0.2, 0.3],
    )

    with get_connection(db_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        insert_chunks(conn, repo_id, tmp_path, [embedded_chunk])

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT repo_id, file_path, start_line, end_line, text, embedding
            FROM chunks
            """
        )
        rows = cursor.fetchall()

        assert len(rows) == 1

        row = rows[0]
        assert row[0] == repo_id
        assert row[1] == "folder/test.py"
        assert row[2] == 1
        assert row[3] == 3
        assert row[4] == "print('hello')"
        assert json.loads(row[5]) == [0.1, 0.2, 0.3]


def test_insert_chunks_multiple_rows(tmp_path):
    db_path = tmp_path / ".repowraith" / "index.db"

    chunk_1 = Chunk(
        file_path=tmp_path / "folder" / "one.py",
        start_line=1,
        end_line=3,
        text="print('one')",
    )

    chunk_2 = Chunk(
        file_path=tmp_path / "folder" / "two.py",
        start_line=4,
        end_line=6,
        text="print('two')",
    )

    embedded_chunk_1 = EmbeddedChunk(
        chunk=chunk_1,
        embedding=[0.1, 0.2, 0.3],
    )

    embedded_chunk_2 = EmbeddedChunk(
        chunk=chunk_2,
        embedding=[0.4, 0.5, 0.6],
    )

    with get_connection(db_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        insert_chunks(
            conn,
            repo_id,
            tmp_path,
            [embedded_chunk_1, embedded_chunk_2],
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT repo_id, file_path, start_line, end_line, text, embedding
            FROM chunks
            ORDER BY file_path
            """
        )
        rows = cursor.fetchall()

        assert len(rows) == 2
        assert {row[1] for row in rows} == {"folder/one.py", "folder/two.py"}
