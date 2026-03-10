from pathlib import Path
from unittest.mock import call, patch

import pytest

from repowraith.embed import EmbeddedChunk, embed_chunks
from repowraith.splitter import Chunk


def test_embed_chunks_returns_embedded_chunks() -> None:
    chunks = [
        Chunk(
            file_path=Path("a.py"),
            start_line=1,
            end_line=3,
            text="print('hello')",
        ),
        Chunk(
            file_path=Path("b.py"),
            start_line=4,
            end_line=6,
            text="print('goodbye')",
        ),
    ]

    with patch("repowraith.embed.embed_text") as mock_embed_text:
        mock_embed_text.side_effect = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]

        result = embed_chunks(chunks)

    assert len(result) == 2
    assert all(isinstance(item, EmbeddedChunk) for item in result)

    assert result[0].chunk == chunks[0]
    assert result[0].embedding == [0.1, 0.2, 0.3]

    assert result[1].chunk == chunks[1]
    assert result[1].embedding == [0.4, 0.5, 0.6]

    mock_embed_text.assert_has_calls(
        [
            call("print('hello')"),
            call("print('goodbye')"),
        ]
    )


def test_embed_chunks_returns_empty_list_for_no_chunks() -> None:
    result = embed_chunks([])

    assert result == []


def test_embed_chunks_raises_if_embed_text_fails() -> None:
    chunks = [
        Chunk(
            file_path=Path("a.py"),
            start_line=1,
            end_line=3,
            text="print('hello')",
        )
    ]

    with patch("repowraith.embed.embed_text", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            embed_chunks(chunks)
