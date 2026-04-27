from pathlib import Path

from repollama.models import Chunk, EmbeddedChunk, RetrievedChunk
from repollama.prompt import build_prompt, format_chunk


def make_retrieved_chunk(
    file_path: str,
    start_line: int,
    end_line: int,
    text: str,
    score: float = 0.9,
) -> RetrievedChunk:
    chunk = Chunk(
        file_path=Path(file_path),
        start_line=start_line,
        end_line=end_line,
        text=text,
    )
    embedded_chunk = EmbeddedChunk(
        chunk=chunk,
        embedding=[0.1, 0.2, 0.3],
    )
    return RetrievedChunk(
        embedded_chunk=embedded_chunk,
        score=score,
    )


def test_format_chunk():
    retrieved_chunk = make_retrieved_chunk(
        "repollama/embed.py",
        10,
        20,
        "def embed_text(text):\n    return [0.1, 0.2]",
    )

    result = format_chunk(retrieved_chunk, 1)

    assert result == (
        "--- [1] repollama/embed.py:10-20 ---\n"
        "def embed_text(text):\n    return [0.1, 0.2]"
    )


def test_build_prompt_includes_question_and_context():
    retrieved_chunks = [
        make_retrieved_chunk(
            "repollama/embed.py",
            10,
            20,
            "def embed_text(text):\n    return [0.1, 0.2]",
        ),
        make_retrieved_chunk(
            "repollama/cli.py",
            30,
            40,
            "def main():\n    pass",
        ),
    ]

    _system, user = build_prompt(
        "Where is embedding implemented?",
        retrieved_chunks,
    )

    assert "Where is embedding implemented?" in user
    assert "[1] repollama/embed.py:10-20" in user
    assert "def embed_text(text):" in user
    assert "[2] repollama/cli.py:30-40" in user
    assert "def main():" in user


def test_build_prompt_only_includes_top_k_chunks():
    retrieved_chunks = [
        make_retrieved_chunk("a.py", 1, 5, "chunk a"),
        make_retrieved_chunk("b.py", 6, 10, "chunk b"),
        make_retrieved_chunk("c.py", 11, 15, "chunk c"),
    ]

    _system, user = build_prompt(
        "Test question",
        retrieved_chunks,
        k=2,
    )

    assert "[1] a.py:1-5" in user
    assert "[2] b.py:6-10" in user
    assert "chunk a" in user
    assert "chunk b" in user

    assert "c.py:11-15" not in user
    assert "chunk c" not in user


def test_build_prompt_numbers_chunks_from_one():
    retrieved_chunks = [
        make_retrieved_chunk("a.py", 1, 5, "chunk a"),
        make_retrieved_chunk("b.py", 6, 10, "chunk b"),
    ]

    _system, user = build_prompt(
        "Test question",
        retrieved_chunks,
    )

    assert "[1] a.py:1-5" in user
    assert "[2] b.py:6-10" in user
    assert "[0]" not in user


def test_build_prompt_with_no_chunks():
    _system, user = build_prompt(
        "Where is embedding implemented?",
        [],
    )

    assert "Where is embedding implemented?" in user
    assert "[1]" not in user
