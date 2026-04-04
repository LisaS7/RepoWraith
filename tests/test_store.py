import datetime
import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from repowraith.models import Chunk, EmbeddedChunk
from repowraith.store import (
    delete_chunks_for_repo,
    get_connection,
    get_db_path,
    get_repo_id,
    index_repository,
    init_db,
    insert_chunks,
    load_chunks,
    upsert_repository,
)


def test_get_db_path(tmp_path) -> None:
    assert get_db_path(tmp_path) == tmp_path / ".repowraith" / "index.db"


def test_get_connection(tmp_path) -> None:
    db_path = tmp_path / ".repowraith" / "index.db"

    with get_connection(tmp_path) as conn:
        assert (tmp_path / ".repowraith").exists()
        assert db_path.exists()
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory is sqlite3.Row


def test_init_db(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

    assert "repositories" in tables
    assert "chunks" in tables
    assert "idx_chunks_repo_id" in indexes


def test_upsert_repository_inserts_row(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        cursor = conn.cursor()
        cursor.execute("SELECT id, root_path, indexed_at FROM repositories")
        rows = cursor.fetchall()

        assert len(rows) == 1

        row = rows[0]
        assert row["id"] == repo_id
        assert row["root_path"] == str(tmp_path.resolve())
        assert row["indexed_at"] is not None


def test_upsert_repository_does_not_duplicate(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        cursor = conn.cursor()

        repo_id_2 = upsert_repository(conn, tmp_path)
        cursor.execute("SELECT id FROM repositories")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert repo_id_2 == repo_id
        assert rows[0]["id"] == repo_id


def test_upsert_repository_updates_indexed_at(tmp_path) -> None:
    t1 = datetime.datetime(2024, 1, 1, 12, 0, 0)
    t2 = datetime.datetime(2024, 1, 1, 12, 0, 1)

    with get_connection(tmp_path) as conn:
        init_db(conn)

        with patch("repowraith.store.datetime.datetime") as mock_dt:
            mock_dt.now.side_effect = [t1, t2]

            upsert_repository(conn, tmp_path)

            cursor = conn.cursor()
            cursor.execute("SELECT indexed_at FROM repositories")
            first_indexed_at = cursor.fetchone()["indexed_at"]

            upsert_repository(conn, tmp_path)

            cursor.execute("SELECT indexed_at FROM repositories")
            second_indexed_at = cursor.fetchone()["indexed_at"]

    assert first_indexed_at == t1.isoformat()
    assert second_indexed_at == t2.isoformat()


def test_get_repo_id_returns_existing_repo_id(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)

        result = get_repo_id(conn, tmp_path)

        assert result == repo_id


def test_get_repo_id_raises_for_missing_repo(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)

        with pytest.raises(ValueError, match="Repository not found in index"):
            get_repo_id(conn, tmp_path)


def test_delete_chunks_for_repo(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
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

        cursor.execute("SELECT COUNT(*) AS count FROM chunks")
        assert cursor.fetchone()["count"] == 3

        delete_chunks_for_repo(conn, repo_id_1)

        cursor.execute("SELECT COUNT(*) AS count FROM chunks")
        assert cursor.fetchone()["count"] == 1

        cursor.execute("SELECT repo_id, file_path FROM chunks")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0]["repo_id"] == repo_id_2
        assert rows[0]["file_path"] == "other.py"


def test_insert_chunks_single_row(tmp_path) -> None:
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

    with get_connection(tmp_path) as conn:
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
        assert row["repo_id"] == repo_id
        assert row["file_path"] == "folder/test.py"
        assert row["start_line"] == 1
        assert row["end_line"] == 3
        assert row["text"] == "print('hello')"
        assert json.loads(row["embedding"]) == [0.1, 0.2, 0.3]


def test_insert_chunks_multiple_rows(tmp_path) -> None:
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

    with get_connection(tmp_path) as conn:
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
        assert {row["file_path"] for row in rows} == {"folder/one.py", "folder/two.py"}


def test_index_repository_replaces_chunks_on_reingest(tmp_path) -> None:
    def make_chunk(filename: str, text: str) -> EmbeddedChunk:
        return EmbeddedChunk(
            chunk=Chunk(
                file_path=tmp_path / filename,
                start_line=1,
                end_line=3,
                text=text,
            ),
            embedding=[0.1, 0.2, 0.3],
        )

    index_repository(tmp_path, [make_chunk("v1.py", "first ingest")])
    index_repository(tmp_path, [make_chunk("v2.py", "second ingest")])

    chunks = load_chunks(tmp_path)

    assert len(chunks) == 1
    assert chunks[0].chunk.text == "second ingest"


# ═════════════════ load_chunks ═════════════════


def test_load_chunks(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(
                    file_path=tmp_path / "repowraith/embed.py",
                    start_line=10,
                    end_line=25,
                    text="def embed_text(text): ...",
                ),
                embedding=[0.1, 0.2, 0.3],
            )
        ])

    chunks = load_chunks(tmp_path)

    assert len(chunks) == 1

    embedded_chunk = chunks[0]
    assert embedded_chunk.chunk.file_path == Path("repowraith/embed.py")
    assert embedded_chunk.chunk.start_line == 10
    assert embedded_chunk.chunk.end_line == 25
    assert embedded_chunk.chunk.text == "def embed_text(text): ..."
    assert embedded_chunk.embedding == [0.1, 0.2, 0.3]


def test_load_chunks_returns_empty_list_when_no_chunks_exist(tmp_path) -> None:
    with get_connection(tmp_path) as conn:
        init_db(conn)
        upsert_repository(conn, tmp_path)

    chunks = load_chunks(tmp_path)

    assert chunks == []
