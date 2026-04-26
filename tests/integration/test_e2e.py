import pytest

from repowraith.embed import embed_chunks
from repowraith.llm import ask_llm
from repowraith.prompt import build_prompt
from repowraith.retrieve import retrieve
from repowraith.splitter import split_repository
from repowraith.store import get_connection, index_repository
from repowraith.survey import survey_repository


@pytest.mark.integration
def test_full_pipeline(tmp_path):
    (tmp_path / "README.md").write_text(
        "# Test repo\nThis project demonstrates indexing.\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "def main():\n    print('hello world')\n",
        encoding="utf-8",
    )
    (tmp_path / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    # Survey
    files = survey_repository(tmp_path)
    assert len(files) == 2

    # Split
    chunks = split_repository(files)
    assert len(chunks) > 0

    # Embed
    embedded_chunks = embed_chunks(chunks)
    assert len(embedded_chunks) == len(chunks)

    # Store
    index_repository(tmp_path, embedded_chunks)

    with get_connection(tmp_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM repositories")
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT COUNT(*) FROM chunks")
        assert cursor.fetchone()[0] == len(chunks)

    # Retrieve
    retrieved_chunks = retrieve("Where is the hello world code?", tmp_path, k=3)
    assert len(retrieved_chunks) > 0
    assert len(retrieved_chunks) <= 3

    # Prompt
    system, user = build_prompt("Where is hello world printed?", retrieved_chunks, k=3)
    assert len(system) > 0
    assert len(user) > 0
    assert "hello world" in user

    # LLM
    answer = ask_llm(system, user)
    assert len(answer) > 0
