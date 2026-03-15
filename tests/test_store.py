import sqlite3
import time

from repowraith.store import get_connection, init_db, upsert_repository


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
