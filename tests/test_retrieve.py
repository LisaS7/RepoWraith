import json
from pathlib import Path

import pytest

from repowraith.retrieve import cosine_similarity, load_chunks, retrieve_chunks
from repowraith.store import get_connection, init_db


def insert_repository(cursor, repo_path: Path) -> int:
    cursor.execute(
        """
        INSERT INTO repositories (root_path, indexed_at)
        VALUES (?, ?)
        """,
        (str(repo_path.resolve()), "2026-03-18T12:00:00"),
    )
    return cursor.lastrowid


def insert_chunk(
    cursor,
    repo_id: int,
    file_path: str,
    start_line: int,
    end_line: int,
    text: str,
    embedding: list[float],
) -> None:
    cursor.execute(
        """
        INSERT INTO chunks (repo_id, file_path, start_line, end_line, text, embedding)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            repo_id,
            file_path,
            start_line,
            end_line,
            text,
            json.dumps(embedding),
        ),
    )


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1)
    assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1)


def test_load_chunks(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        repo_id = insert_repository(cursor, tmp_path)

        insert_chunk(
            cursor,
            repo_id,
            "repowraith/embed.py",
            10,
            25,
            "def embed_text(text): ...",
            [0.1, 0.2, 0.3],
        )
        conn.commit()

    chunks = load_chunks(tmp_path)

    assert len(chunks) == 1

    embedded_chunk = chunks[0]
    assert embedded_chunk.chunk.file_path == Path("repowraith/embed.py")
    assert embedded_chunk.chunk.start_line == 10
    assert embedded_chunk.chunk.end_line == 25
    assert embedded_chunk.chunk.text == "def embed_text(text): ..."
    assert embedded_chunk.embedding == [0.1, 0.2, 0.3]


def test_retrieve_chunks_returns_best_match_first(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        repo_id = insert_repository(cursor, tmp_path)

        insert_chunk(cursor, repo_id, "good_match.py", 1, 10, "best chunk", [1.0, 0.0])
        insert_chunk(cursor, repo_id, "bad_match.py", 1, 10, "worse chunk", [0.0, 1.0])

        conn.commit()

    results = retrieve_chunks([1.0, 0.0], tmp_path, k=2)

    assert len(results) == 2
    assert results[0].embedded_chunk.chunk.file_path == Path("good_match.py")
    assert results[0].score == pytest.approx(1.0)
    assert results[1].embedded_chunk.chunk.file_path == Path("bad_match.py")
    assert results[1].score == pytest.approx(0.0)
