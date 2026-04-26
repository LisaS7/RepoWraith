from pathlib import Path

from repowraith.models import Chunk, EmbeddedChunk, RetrievedChunk
from repowraith.prompt import build_prompt, format_chunk


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
        "repowraith/embed.py",
        10,
        20,
        "def embed_text(text):\n    return [0.1, 0.2]",
    )

    result = format_chunk(retrieved_chunk, 1)

    assert result == (
        "--- [1] repowraith/embed.py:10-20 ---\n"
        "def embed_text(text):\n    return [0.1, 0.2]"
    )


def test_build_prompt_includes_question_and_context():
    retrieved_chunks = [
        make_retrieved_chunk(
            "repowraith/embed.py",
            10,
            20,
            "def embed_text(text):\n    return [0.1, 0.2]",
        ),
        make_retrieved_chunk(
            "repowraith/cli.py",
            30,
            40,
            "def main():\n    pass",
        ),
    ]

    result = build_prompt(
        "Where is embedding implemented?",
        retrieved_chunks,
    )

    assert "Where is embedding implemented?" in result
    assert "[1] repowraith/embed.py:10-20" in result
    assert "def embed_text(text):" in result
    assert "[2] repowraith/cli.py:30-40" in result
    assert "def main():" in result


def test_build_prompt_only_includes_top_k_chunks():
    retrieved_chunks = [
        make_retrieved_chunk("a.py", 1, 5, "chunk a"),
        make_retrieved_chunk("b.py", 6, 10, "chunk b"),
        make_retrieved_chunk("c.py", 11, 15, "chunk c"),
    ]

    result = build_prompt(
        "Test question",
        retrieved_chunks,
        k=2,
    )

    assert "[1] a.py:1-5" in result
    assert "[2] b.py:6-10" in result
    assert "chunk a" in result
    assert "chunk b" in result

    assert "c.py:11-15" not in result
    assert "chunk c" not in result


def test_build_prompt_numbers_chunks_from_one():
    retrieved_chunks = [
        make_retrieved_chunk("a.py", 1, 5, "chunk a"),
        make_retrieved_chunk("b.py", 6, 10, "chunk b"),
    ]

    result = build_prompt(
        "Test question",
        retrieved_chunks,
    )

    assert "[1] a.py:1-5" in result
    assert "[2] b.py:6-10" in result
    assert "[0]" not in result


def test_build_prompt_with_no_chunks():
    result = build_prompt(
        "Where is embedding implemented?",
        [],
    )

    assert "Where is embedding implemented?" in result
    assert "[1]" not in result
