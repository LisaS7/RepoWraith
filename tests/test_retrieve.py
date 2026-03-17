import json

import pytest

from repowraith.retrieve import cosine_similarity, load_chunks
from repowraith.store import get_connection, init_db


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1)
    assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1)


def test_load_chunks(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chunks (repo_id, file_path, start_line, end_line, text, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "repowraith/embed.py",
                10,
                25,
                "def embed_text(text): ...",
                json.dumps([0.1, 0.2, 0.3]),
            ),
        )
        conn.commit()

    chunks = load_chunks(tmp_path)

    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk.file_path == "repowraith/embed.py"
    assert chunk.start_line == 10
    assert chunk.end_line == 25
    assert chunk.text == "def embed_text(text): ..."
    assert chunk.embedding == [0.1, 0.2, 0.3]
