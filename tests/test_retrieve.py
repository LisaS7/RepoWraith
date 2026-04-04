from pathlib import Path

import pytest

from repowraith.models import Chunk, EmbeddedChunk
from repowraith.retrieve import (
    bm25_score,
    compute_document_frequencies,
    cosine_similarity,
    filename_score,
    is_test_file,
    query_is_about_tests,
    retrieve_chunks,
    tokenize,
    tokenize_query,
)
from repowraith.store import get_connection, init_db, insert_chunks, load_chunks, upsert_repository


# ═════════════════ tokenize ═════════════════


def test_tokenize_lowercases_and_strips_non_alphanumeric():
    assert tokenize("Hello WORLD\tfriend") == ["hello", "world", "friend"]


def test_tokenize_expands_underscores_into_sub_tokens():
    assert tokenize("embed_text") == ["embed_text", "embed", "text"]


def test_tokenize_skips_empty_parts_from_leading_trailing_underscores():
    assert tokenize("_private_") == ["_private_", "private"]


def test_tokenize_splits_camelcase():
    assert tokenize("MyClass") == ["my", "class"]


def test_tokenize_splits_camelcase_lowercase_start():
    assert tokenize("retrieveChunks") == ["retrieve", "chunks"]


def test_tokenize_splits_camelcase_multiple_humps():
    assert tokenize("EmbeddedChunkStore") == ["embedded", "chunk", "store"]


def test_tokenize_query_strips_stop_words():
    # "how", "the", "work" are stop words; "retrieval" is not
    result = tokenize_query("how does the retrieval work")
    assert "retrieval" in result
    assert "how" not in result
    assert "the" not in result
    assert "work" not in result


# ═════════════════ cosine_similarity ═════════════════


def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0)
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1)
    assert cosine_similarity([1, 2], [2, 4]) == pytest.approx(1)


def test_cosine_similarity_zero_vector_returns_zero():
    assert cosine_similarity([0, 0], [1, 0]) == 0.0
    assert cosine_similarity([1, 0], [0, 0]) == 0.0


# ═════════════════ compute_document_frequencies ═════════════════


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


# ═════════════════ load_chunks ═════════════════


def test_load_chunks(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(
                    file_path=tmp_path / "repowraith/embed.py",
                    start_line=10,
                    end_line=25,
                    text="def embed_text(text): ...",
                ),
                embedding=[0.1, 0.2, 0.3],
            )
        ])

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
        upsert_repository(conn, tmp_path)

    chunks = load_chunks(tmp_path)

    assert chunks == []


# ═════════════════ retrieve_chunks ═════════════════


def test_retrieve_chunks_returns_best_match_first(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(file_path=tmp_path / "good_match.py", start_line=1, end_line=10, text="best chunk"),
                embedding=[1.0, 0.0],
            ),
            EmbeddedChunk(
                chunk=Chunk(file_path=tmp_path / "bad_match.py", start_line=1, end_line=10, text="worse chunk"),
                embedding=[0.0, 1.0],
            ),
        ])

    results = retrieve_chunks("best chunk", [1.0, 0.0], tmp_path, k=2)

    assert len(results) == 2
    assert results[0].chunk.file_path == Path("good_match.py")
    assert results[1].chunk.file_path == Path("bad_match.py")
    assert results[0].score > results[1].score


def test_retrieve_chunks_returns_empty_list_for_empty_repo(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        upsert_repository(conn, tmp_path)

    results = retrieve_chunks("sqlite", [1.0, 0.0], tmp_path)

    assert results == []


def test_retrieve_chunks_respects_k(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(file_path=tmp_path / "a.py", start_line=1, end_line=10, text="chunk a"),
                embedding=[1.0, 0.0],
            ),
            EmbeddedChunk(
                chunk=Chunk(file_path=tmp_path / "b.py", start_line=1, end_line=10, text="chunk b"),
                embedding=[0.9, 0.1],
            ),
            EmbeddedChunk(
                chunk=Chunk(file_path=tmp_path / "c.py", start_line=1, end_line=10, text="chunk c"),
                embedding=[0.8, 0.2],
            ),
        ])

    results = retrieve_chunks("chunk", [1.0, 0.0], tmp_path, k=2)

    assert len(results) == 2


# ═════════════════ bm25_score ═════════════════


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


# ═════════════════ filename_score ═════════════════


def test_filename_score_exact_term_match():
    assert filename_score("retrieve chunks", "repowraith/retrieve.py") > 0.0


def test_filename_score_no_match():
    assert filename_score("banana lamp", "repowraith/retrieve.py") == 0.0


def test_filename_score_substring_match_long_token():
    # "config" (len 6 >= 4) is a substring of query term "configs"
    assert filename_score("configs", "repowraith/config.py") > 0.0


def test_filename_score_short_token_not_used_as_substring():
    # "py" (len 2 < 4) should not substring-match inside the query term "types"
    # even though "py" literally appears in "types"
    assert filename_score("types", "src/a.py") == 0.0


def test_filename_score_query_term_is_prefix_of_path_token():
    # "split" (len 5 >= 4) is a substring of path token "splitter"
    assert filename_score("split file function", "repowraith/splitter.py") > 0.0


# ═════════════════ is_test_file ═════════════════


def test_is_test_file_tests_directory():
    assert is_test_file("tests/test_retrieve.py") is True


def test_is_test_file_test_prefix():
    assert is_test_file("src/test_utils.py") is True


def test_is_test_file_test_suffix():
    assert is_test_file("src/utils_test.py") is True


def test_is_test_file_normal_file():
    assert is_test_file("repowraith/retrieve.py") is False


# ═════════════════ query_is_about_tests ═════════════════


def test_query_is_about_tests_returns_true_for_test_keywords():
    assert query_is_about_tests("where are the tests") is True
    assert query_is_about_tests("how does testing work") is True
    assert query_is_about_tests("find the test for retrieval") is True


def test_query_is_about_tests_returns_false_for_unrelated_query():
    assert query_is_about_tests("how does retrieval work") is False
    assert query_is_about_tests("where is the config file") is False


# ═════════════════ test-file penalty ═════════════════


def test_retrieve_chunks_penalizes_test_files_for_non_test_query(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(
                    file_path=tmp_path / "tests/test_retrieve.py",
                    start_line=1,
                    end_line=10,
                    text="def test_foo(): pass",
                ),
                embedding=[1.0, 0.0],
            ),
        ])

    results = retrieve_chunks("how does retrieval work", [1.0, 0.0], tmp_path, k=1)

    assert results[0].test_penalized is True


def test_retrieve_chunks_does_not_penalize_test_files_for_test_query(tmp_path):
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(
                    file_path=tmp_path / "tests/test_retrieve.py",
                    start_line=1,
                    end_line=10,
                    text="def test_foo(): pass",
                ),
                embedding=[1.0, 0.0],
            ),
        ])

    results = retrieve_chunks("where are the tests", [1.0, 0.0], tmp_path, k=1)

    assert results[0].test_penalized is False


# ═════════════════ filename ranking ═════════════════


def test_retrieve_chunks_filename_match_boosts_ranking(tmp_path):
    # Both chunks have identical text and embeddings, so semantic and lexical
    # scores are equal. The chunk whose filename matches the query should rank
    # higher due to the filename score contribution.
    with get_connection(tmp_path) as conn:
        init_db(conn)
        repo_id = upsert_repository(conn, tmp_path)
        insert_chunks(conn, repo_id, tmp_path, [
            EmbeddedChunk(
                chunk=Chunk(
                    file_path=tmp_path / "retrieve.py",
                    start_line=1,
                    end_line=5,
                    text="some generic code",
                ),
                embedding=[1.0, 0.0],
            ),
            EmbeddedChunk(
                chunk=Chunk(
                    file_path=tmp_path / "unrelated.py",
                    start_line=1,
                    end_line=5,
                    text="some generic code",
                ),
                embedding=[1.0, 0.0],
            ),
        ])

    results = retrieve_chunks("retrieve chunks", [1.0, 0.0], tmp_path, k=2)

    file_paths = [str(r.chunk.file_path) for r in results]
    assert file_paths.index("retrieve.py") < file_paths.index("unrelated.py")
