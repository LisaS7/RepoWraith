import json
from pathlib import Path

import pytest

from repowraith.models import Chunk, EmbeddedChunk
from repowraith.retrieve import (
    bm25_score,
    compute_document_frequencies,
    cosine_similarity,
    retrieve_chunks,
    tokenize,
)
from repowraith.store import get_connection, init_db, load_chunks


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


def test_tokenize_lowercases_and_splits_on_whitespace():
    assert tokenize("Hello WORLD\tfriend") == ["hello", "world", "friend"]


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1)
    assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1)


def test_compute_document_frequencies_counts_each_term_once_per_document():
    chunks = [
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("a.py"),
                start_line=1,
                end_line=1,
                text="sqlite sqlite sqlite",
            ),
            embedding=[0.0],
        ),
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("b.py"),
                start_line=1,
                end_line=1,
                text="sqlite retrieval",
            ),
            embedding=[0.0],
        ),
    ]

    doc_freqs = compute_document_frequencies([tokenize(c.chunk.text) for c in chunks])

    assert doc_freqs["sqlite"] == 2
    assert doc_freqs["retrieval"] == 1


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


def test_load_chunks_returns_empty_list_when_no_chunks_exist(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        insert_repository(cursor, tmp_path)
        conn.commit()

    chunks = load_chunks(tmp_path)

    assert chunks == []


def test_retrieve_chunks_returns_best_match_first(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        repo_id = insert_repository(cursor, tmp_path)

        insert_chunk(cursor, repo_id, "good_match.py", 1, 10, "best chunk", [1.0, 0.0])
        insert_chunk(cursor, repo_id, "bad_match.py", 1, 10, "worse chunk", [0.0, 1.0])

        conn.commit()

    results = retrieve_chunks("best chunk", [1.0, 0.0], tmp_path, k=2)

    assert len(results) == 2
    assert results[0].embedded_chunk.chunk.file_path == Path("good_match.py")
    assert results[1].embedded_chunk.chunk.file_path == Path("bad_match.py")
    assert results[0].score > results[1].score


def test_retrieve_chunks_returns_empty_list_for_empty_repo(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        insert_repository(cursor, tmp_path)
        conn.commit()

    results = retrieve_chunks("sqlite", [1.0, 0.0], tmp_path)

    assert results == []


def test_retrieve_chunks_respects_k(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        cursor = conn.cursor()
        repo_id = insert_repository(cursor, tmp_path)

        insert_chunk(cursor, repo_id, "a.py", 1, 10, "chunk a", [1.0, 0.0])
        insert_chunk(cursor, repo_id, "b.py", 1, 10, "chunk b", [0.9, 0.1])
        insert_chunk(cursor, repo_id, "c.py", 1, 10, "chunk c", [0.8, 0.2])
        conn.commit()

    results = retrieve_chunks("chunk", [1.0, 0.0], tmp_path, k=2)

    assert len(results) == 2


def test_bm25_scores_matching_text_higher():
    matching_text = "sqlite repo sqlite retrieval"
    non_matching_text = "banana lamp velvet octopus"

    chunks = [
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("a.py"),
                start_line=1,
                end_line=1,
                text=matching_text,
            ),
            embedding=[0.0],
        ),
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("b.py"),
                start_line=1,
                end_line=1,
                text=non_matching_text,
            ),
            embedding=[0.0],
        ),
    ]

    tokenized_texts = [tokenize(c.chunk.text) for c in chunks]
    document_frequencies = compute_document_frequencies(tokenized_texts)
    total_docs = len(chunks)
    average_doc_length = sum(len(t) for t in tokenized_texts) / total_docs

    matching_score = bm25_score(
        query="sqlite repo",
        tokens=tokenize(matching_text),
        document_frequencies=document_frequencies,
        total_docs=total_docs,
        average_doc_length=average_doc_length,
    )
    non_matching_score = bm25_score(
        query="sqlite repo",
        tokens=tokenize(non_matching_text),
        document_frequencies=document_frequencies,
        total_docs=total_docs,
        average_doc_length=average_doc_length,
    )

    assert matching_score > non_matching_score


def test_bm25_rewards_higher_term_frequency():
    text_with_one = "sqlite retrieval engine"
    text_with_three = "sqlite sqlite sqlite retrieval engine"

    chunks = [
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("a.py"),
                start_line=1,
                end_line=1,
                text=text_with_one,
            ),
            embedding=[0.0],
        ),
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("b.py"),
                start_line=1,
                end_line=1,
                text=text_with_three,
            ),
            embedding=[0.0],
        ),
    ]

    tokenized_texts = [tokenize(c.chunk.text) for c in chunks]
    document_frequencies = compute_document_frequencies(tokenized_texts)
    total_docs = len(chunks)
    average_doc_length = sum(len(t) for t in tokenized_texts) / total_docs

    score_one = bm25_score(
        query="sqlite",
        tokens=tokenize(text_with_one),
        document_frequencies=document_frequencies,
        total_docs=total_docs,
        average_doc_length=average_doc_length,
    )
    score_three = bm25_score(
        query="sqlite",
        tokens=tokenize(text_with_three),
        document_frequencies=document_frequencies,
        total_docs=total_docs,
        average_doc_length=average_doc_length,
    )

    assert score_three > score_one


def test_bm25_score_is_zero_when_query_terms_are_absent():
    chunks = [
        EmbeddedChunk(
            chunk=Chunk(
                file_path=Path("a.py"),
                start_line=1,
                end_line=1,
                text="banana lamp velvet octopus",
            ),
            embedding=[0.0],
        )
    ]

    document_frequencies = compute_document_frequencies([tokenize(c.chunk.text) for c in chunks])

    score = bm25_score(
        query="sqlite repo",
        tokens=tokenize("banana lamp velvet octopus"),
        document_frequencies=document_frequencies,
        total_docs=1,
        average_doc_length=4,
    )

    assert score == pytest.approx(0.0)
