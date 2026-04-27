from pathlib import Path

import pytest

from repollama.errors import OllamaResponseError
from repollama.models import Chunk, EmbeddedChunk, RetrievedChunk
from repollama.rerank import rerank_chunks, score_chunk


def _make_retrieved(text: str = "some text", score: float = 0.5) -> RetrievedChunk:
    chunk = Chunk(file_path=Path("file.py"), start_line=1, end_line=10, text=text)
    embedded = EmbeddedChunk(chunk=chunk, embedding=[0.1, 0.2])
    return RetrievedChunk(embedded_chunk=embedded, score=score)


def _ollama_response(content: str) -> dict:
    return {"message": {"content": content}}


# ═════════════════ score_chunk ═════════════════


def test_score_chunk_parses_bare_integer(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: _ollama_response("8"),
    )
    score = score_chunk("question", _make_retrieved())
    assert score == 0.8


def test_score_chunk_parses_score_with_surrounding_text(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: _ollama_response("Score: 7"),
    )
    score = score_chunk("question", _make_retrieved())
    assert score == 0.7


def test_score_chunk_handles_ten_out_of_ten(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: _ollama_response("10/10"),
    )
    score = score_chunk("question", _make_retrieved())
    assert score == 1.0


def test_score_chunk_handles_zero(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: _ollama_response("0"),
    )
    score = score_chunk("question", _make_retrieved())
    assert score == 0.0


def test_score_chunk_returns_zero_when_no_integer_present(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: _ollama_response("not sure, no clear answer"),
    )
    score = score_chunk("question", _make_retrieved())
    assert score == 0.0


def test_score_chunk_raises_when_response_missing_content(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: {"message": {}},
    )
    with pytest.raises(OllamaResponseError):
        score_chunk("question", _make_retrieved())


# ═════════════════ rerank_chunks ═════════════════


def test_rerank_chunks_sorts_by_rerank_score(monkeypatch):
    a = _make_retrieved(text="alpha", score=0.1)
    b = _make_retrieved(text="bravo", score=0.9)  # high retrieve score, low rerank
    c = _make_retrieved(text="charlie", score=0.5)

    score_by_text = {"alpha": "5", "bravo": "1", "charlie": "9"}

    def fake_post(url, body, **kw):
        excerpt = body["messages"][1]["content"]
        for key, value in score_by_text.items():
            if key in excerpt:
                return _ollama_response(value)
        return _ollama_response("0")

    monkeypatch.setattr("repollama.rerank.post_to_ollama", fake_post)

    result = rerank_chunks("question", [a, b, c])

    assert [rc.chunk.text for rc in result] == ["charlie", "alpha", "bravo"]
    assert result[0].rerank_score == 0.9
    assert result[1].rerank_score == 0.5
    assert result[2].rerank_score == 0.1


def test_rerank_chunks_empty_list_returns_empty(monkeypatch):
    monkeypatch.setattr(
        "repollama.rerank.post_to_ollama",
        lambda *a, **kw: _ollama_response("5"),
    )
    assert rerank_chunks("question", []) == []
