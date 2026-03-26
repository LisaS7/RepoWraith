import json
import math
from pathlib import Path

from repowraith.embed import embed_text
from repowraith.models import Chunk, EmbeddedChunk, RetrievedChunk
from repowraith.store import get_connection, get_repo_id


def tokenize(text: str) -> list[str]:
    return text.lower().split()


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
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    score = 0.0
    query_terms = tokenize(query)
    doc_length = len(tokenize(text))

    for term in query_terms:
        tf = term_frequency(term, text)
        if tf == 0:
            continue

        doc_freq = document_frequencies.get(term, 0)
        idf = inverse_document_frequency(term, total_docs, doc_freq)

        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_length / average_doc_length))

        score += idf * (numerator / denominator)

    return score


def load_chunks(repo_path: Path) -> list[EmbeddedChunk]:

    with get_connection(repo_path) as conn:
        repo_id = get_repo_id(conn, repo_path)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT file_path, start_line, end_line, text, embedding FROM chunks WHERE repo_id = {repo_id}"
        )
        rows = cursor.fetchall()

    chunks = []
    for row in rows:
        chunk = Chunk(
            file_path=Path(row["file_path"]),
            start_line=row["start_line"],
            end_line=row["end_line"],
            text=row["text"],
        )
        embedded_chunk = EmbeddedChunk(
            chunk=chunk,
            embedding=json.loads(row["embedding"]),
        )
        chunks.append(embedded_chunk)

    return chunks


def retrieve_chunks(
    query: str,
    query_embedding: list[float],
    repo_path: Path,
    k: int = 5,
    verbose: bool = False,
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

    chunks = []
    for embedded_chunk in embedded_chunks:
        semantic_score = cosine_similarity(query_embedding, embedded_chunk.embedding)
        lexical_score = bm25_score(
            query=query,
            text=embedded_chunk.chunk.text,
            document_frequencies=document_frequencies,
            total_docs=total_docs,
            average_doc_length=average_doc_length,
        )
        score = semantic_score + 0.2 * lexical_score

        if verbose:
            print("\n--- Retrieval Debug ---")
            print(
                f"{embedded_chunk.chunk.file_path}:{embedded_chunk.chunk.start_line}-{embedded_chunk.chunk.end_line} "
                f"semantic={semantic_score:.4f} "
                f"lexical={lexical_score:.4f} "
                f"total={score:.4f}"
            )
            print()

        retrieved_chunk = RetrievedChunk(embedded_chunk=embedded_chunk, score=score)
        chunks.append(retrieved_chunk)
    chunks.sort(key=lambda chunk: chunk.score, reverse=True)

    return chunks[:k]


def retrieve(
    query: str, repo_path: Path, k: int = 5, verbose: bool = False
) -> list[RetrievedChunk]:
    query_embedding = embed_text(query)
    return retrieve_chunks(query, query_embedding, repo_path, k, verbose=verbose)
