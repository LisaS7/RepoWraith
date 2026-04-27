from pathlib import Path
from unittest.mock import call, patch

import pytest

from repollama.embed import embed_chunks, embed_text
from repollama.errors import OllamaConnectionError, OllamaResponseError
from repollama.models import Chunk, EmbeddedChunk


# ═════════════════ embed_chunks ═════════════════


@patch("repollama.embed.post_to_ollama")
def test_embed_chunks_returns_embedded_chunks(mock_post) -> None:
    chunks = [
        Chunk(file_path=Path("a.py"), start_line=1, end_line=3, text="print('hello')"),
        Chunk(file_path=Path("b.py"), start_line=4, end_line=6, text="print('goodbye')"),
    ]
    mock_post.return_value = {"embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]}

    result = embed_chunks(chunks)

    assert len(result) == 2
    assert all(isinstance(item, EmbeddedChunk) for item in result)
    assert result[0].chunk == chunks[0]
    assert result[0].embedding == [0.1, 0.2, 0.3]
    assert result[1].chunk == chunks[1]
    assert result[1].embedding == [0.4, 0.5, 0.6]
    mock_post.assert_called_once()


def test_embed_chunks_returns_empty_list_for_no_chunks() -> None:
    result = embed_chunks([])

    assert result == []


@patch("repollama.embed.post_to_ollama")
def test_embed_chunks_batches_by_batch_size(mock_post) -> None:
    chunks = [
        Chunk(file_path=Path("a.py"), start_line=1, end_line=1, text="a"),
        Chunk(file_path=Path("b.py"), start_line=2, end_line=2, text="b"),
        Chunk(file_path=Path("c.py"), start_line=3, end_line=3, text="c"),
    ]
    mock_post.side_effect = [
        {"embeddings": [[0.1, 0.2], [0.3, 0.4]]},
        {"embeddings": [[0.5, 0.6]]},
    ]

    with patch("repollama.embed.EMBED_BATCH_SIZE", 2):
        result = embed_chunks(chunks)

    assert len(result) == 3
    assert result[0].embedding == [0.1, 0.2]
    assert result[1].embedding == [0.3, 0.4]
    assert result[2].embedding == [0.5, 0.6]
    assert mock_post.call_count == 2


@patch(
    "repollama.embed.post_to_ollama",
    side_effect=OllamaConnectionError("Ollama not running"),
)
def test_embed_chunks_propagates_ollama_connection_error(mock_post) -> None:
    chunks = [
        Chunk(file_path=Path("a.py"), start_line=1, end_line=3, text="print('hello')")
    ]
    with pytest.raises(OllamaConnectionError, match="Ollama not running"):
        embed_chunks(chunks)


@patch(
    "repollama.embed.post_to_ollama",
    side_effect=OllamaResponseError("bad response"),
)
def test_embed_chunks_propagates_ollama_response_error(mock_post) -> None:
    chunks = [
        Chunk(file_path=Path("a.py"), start_line=1, end_line=3, text="print('hello')")
    ]
    with pytest.raises(OllamaResponseError, match="bad response"):
        embed_chunks(chunks)


# ═════════════════ embed_text ═════════════════


@patch("repollama.embed.post_to_ollama")
def test_embed_text_returns_inner_embedding_vector(mock_post) -> None:
    mock_post.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}

    result = embed_text("hello world")

    assert result == [0.1, 0.2, 0.3]


@patch("repollama.embed.post_to_ollama")
def test_embed_text_raises_when_embeddings_key_missing(mock_post) -> None:
    mock_post.return_value = {}

    with pytest.raises(OllamaResponseError, match="missing non-empty 'embeddings'"):
        embed_text("hello")


@patch("repollama.embed.post_to_ollama")
def test_embed_text_raises_when_embeddings_list_is_empty(mock_post) -> None:
    mock_post.return_value = {"embeddings": []}

    with pytest.raises(OllamaResponseError, match="missing non-empty 'embeddings'"):
        embed_text("hello")


@patch("repollama.embed.post_to_ollama")
def test_embed_text_raises_when_inner_vector_is_empty(mock_post) -> None:
    mock_post.return_value = {"embeddings": [[]]}

    with pytest.raises(OllamaResponseError, match="invalid embedding vector"):
        embed_text("hello")


@patch("repollama.embed.post_to_ollama")
def test_embed_text_raises_when_inner_vector_contains_non_numeric(mock_post) -> None:
    mock_post.return_value = {"embeddings": [["not", "a", "float"]]}

    with pytest.raises(OllamaResponseError, match="non-numeric"):
        embed_text("hello")
