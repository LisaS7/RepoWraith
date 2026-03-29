import logging
import math
import re
from pathlib import Path

from repowraith.config import BM25_B, BM25_K1, DEFAULT_TOP_K, FILENAME_WEIGHT, LEXICAL_WEIGHT, STOP_WORDS, TEST_FILE_WEIGHT
from repowraith.embed import embed_text
from repowraith.models import EmbeddedChunk, RetrievedChunk
from repowraith.store import load_chunks


def tokenize(text: str) -> list[str]:
    raw_tokens = re.findall(r"[a-z0-9_]+", text.lower())
    tokens = []

    for token in raw_tokens:
        tokens.append(token)

        if "_" in token:
            parts = [part for part in token.split("_") if part]
            tokens.extend(parts)

    return tokens


def tokenize_query(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOP_WORDS]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(y * y for y in b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def compute_document_frequencies(chunks: list[EmbeddedChunk]) -> dict[str, int]:
    doc_freqs = {}

    for embedded_chunk in chunks:
        unique_terms = set(tokenize(embedded_chunk.chunk.text))
        for term in unique_terms:
            doc_freqs[term] = doc_freqs.get(term, 0) + 1

    return doc_freqs


def inverse_document_frequency(term: str, total_docs: int, doc_freq: int) -> float:
    return math.log(1 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))


def term_frequency(term: str, text: str) -> int:
    tokens = tokenize(text)
    return tokens.count(term)


def bm25_score(
    query: str,
    text: str,
    document_frequencies: dict[str, int],
    total_docs: int,
    average_doc_length: float,
) -> float:
    score = 0.0
    query_terms = tokenize_query(query)
    doc_length = len(tokenize(text))

    for term in query_terms:
        tf = term_frequency(term, text)
        if tf == 0:
            continue

        doc_freq = document_frequencies.get(term, 0)
        idf = inverse_document_frequency(term, total_docs, doc_freq)

        numerator = tf * (BM25_K1 + 1)
        denominator = tf + BM25_K1 * (
            1 - BM25_B + BM25_B * (doc_length / average_doc_length)
        )

        score += idf * (numerator / denominator)

    return score


def filename_score(query: str, file_path: str) -> float:
    path_tokens = set()
    for part in re.split(r"[/\\.]", file_path):
        path_tokens.update(tokenize(part))

    query_terms = tokenize_query(query)
    # Count how many query terms match at least one path token.
    # A match is either exact ("config" == "config") or a path token that is a
    # substring of the query term ("config" in "configs") — with a min length of
    # 4 to prevent short tokens like "py" from matching words like "types".
    matches = sum(
        1 for term in query_terms
        if any(term == tok or (len(tok) >= 4 and tok in term) for tok in path_tokens)
    )
    return float(matches)


def is_test_file(file_path: str) -> bool:
    parts = re.split(r"[/\\]", file_path)
    return any(p == "tests" or p.startswith("test_") or p.endswith("_test.py") for p in parts)


def query_is_about_tests(query: str) -> bool:
    return bool({"test", "tests", "testing"} & set(tokenize_query(query)))


def retrieve_chunks(
    query: str,
    query_embedding: list[float],
    repo_path: Path,
    k: int = DEFAULT_TOP_K,
) -> list[RetrievedChunk]:
    embedded_chunks = load_chunks(repo_path)
    total_docs = len(embedded_chunks)

    if total_docs == 0:
        return []

    document_frequencies = compute_document_frequencies(embedded_chunks)
    doc_lengths = [
        len(tokenize(embedded_chunk.chunk.text)) for embedded_chunk in embedded_chunks
    ]
    average_doc_length = sum(doc_lengths) / total_docs

    scored_chunks = []
    for embedded_chunk in embedded_chunks:
        semantic_score = cosine_similarity(query_embedding, embedded_chunk.embedding)
        lexical_score = bm25_score(
            query=query,
            text=embedded_chunk.chunk.text,
            document_frequencies=document_frequencies,
            total_docs=total_docs,
            average_doc_length=average_doc_length,
        )
        file_score = filename_score(query, str(embedded_chunk.chunk.file_path))
        score = semantic_score + LEXICAL_WEIGHT * lexical_score + FILENAME_WEIGHT * file_score
        # Test files tend to dominate lexical scoring because they repeat function/variable
        # names from the code they test. Penalise them unless the query is about testing.
        test_penalized = is_test_file(str(embedded_chunk.chunk.file_path)) and not query_is_about_tests(query)
        if test_penalized:
            score *= TEST_FILE_WEIGHT

        retrieved_chunk = RetrievedChunk(embedded_chunk=embedded_chunk, score=score)
        scored_chunks.append(
            {
                "retrieved_chunk": retrieved_chunk,
                "semantic_score": semantic_score,
                "lexical_score": lexical_score,
                "file_score": file_score,
                "test_penalized": test_penalized,
            }
        )

    scored_chunks.sort(
        key=lambda item: item["retrieved_chunk"].score,
        reverse=True,
    )

    logger = logging.getLogger(__name__)
    logger.debug("--- Retrieval Debug ---")
    for item in scored_chunks:
        chunk = item["retrieved_chunk"].embedded_chunk.chunk
        logger.debug(
            "%s:%d-%d semantic=%.4f lexical=%.4f file=%.4f total=%.4f test_penalized=%s",
            chunk.file_path,
            chunk.start_line,
            chunk.end_line,
            item["semantic_score"],
            item["lexical_score"],
            item["file_score"],
            item["retrieved_chunk"].score,
            item["test_penalized"],
        )

    return [item["retrieved_chunk"] for item in scored_chunks[:k]]


def retrieve(query: str, repo_path: Path) -> list[RetrievedChunk]:
    query_embedding = embed_text(query)
    return retrieve_chunks(query, query_embedding, repo_path)
