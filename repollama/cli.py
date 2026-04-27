import argparse
import logging
import sys
from pathlib import Path

from repollama.config import DEFAULT_TOP_K, RERANK_CANDIDATES
from repollama.embed import embed_chunks
from repollama.errors import RepoLlamaError
from repollama.llm import ask_llm
from repollama.prompt import build_prompt
from repollama.rerank import score_chunk
from repollama.retrieve import retrieve
from repollama.splitter import hash_file, split_file
from repollama.store import (
    get_connection,
    get_repo_id,
    index_repository,
    init_db,
    load_chunks_by_file,
)
from repollama.survey import survey_repository


def preview_text(text: str, max_lines: int = 5) -> str:
    lines = text.strip().splitlines()
    preview = lines[:max_lines]

    if len(lines) > max_lines:
        preview.append("...")

    return "\n".join(preview)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="repollama")
    subparsers = parser.add_subparsers(dest="command", required=True)

    survey_parser = subparsers.add_parser(
        "survey", help="Survey a repository and list indexable files"
    )
    survey_parser.add_argument("path", help="Path to the repository root")
    survey_parser.add_argument(
        "--verbose", action="store_true", help="Print discovered file paths"
    )

    ingest_parser = subparsers.add_parser(
        "ingest", help="Index a repository so it can be queried using RepoLlama"
    )
    ingest_parser.add_argument("path", help="Path to the repository root")

    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a question about an indexed repository",
    )
    ask_parser.add_argument("path", help="Path to the repository root")
    ask_parser.add_argument("question", help="Question to ask about the repository")
    ask_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print retrieval debug output",
    )
    ask_parser.set_defaults(func=cmd_ask)

    # Register command functions
    survey_parser.set_defaults(func=cmd_survey)
    ingest_parser.set_defaults(func=cmd_ingest)

    return parser.parse_args(args)


# ═════════════════ COMMAND FUNCTIONS ══════════════════


def cmd_survey(args: argparse.Namespace) -> None:
    files = survey_repository(Path(args.path))

    print(f"{len(files)} files discovered")

    if args.verbose:
        print()
        for file in files:
            print(file.as_posix())


def cmd_ingest(args: argparse.Namespace) -> None:
    repo_path = Path(args.path).resolve()

    print("Surveying repository...")
    files = survey_repository(repo_path)
    print(f"{len(files)} files discovered")
    print()

    # Load existing index so unchanged files can be skipped
    existing_by_file = {}
    try:
        with get_connection(repo_path) as conn:
            init_db(conn)
            repo_id = get_repo_id(conn, repo_path)
            existing_by_file = load_chunks_by_file(conn, repo_id, repo_path)
    except ValueError:
        pass  # No existing index yet — full ingest

    print("Chunking and embedding files...")
    all_embedded = []
    changed = skipped = 0
    total = len(files)

    surveyed_rel_paths = {f.relative_to(repo_path).as_posix() for f in files}
    existing_by_file = {k: v for k, v in existing_by_file.items() if k in surveyed_rel_paths}

    for i, file in enumerate(files, start=1):
        rel_path = file.relative_to(repo_path).as_posix()
        print(f"  [{i}/{total}] {rel_path}", flush=True)
        current_hash = hash_file(file)
        stored = existing_by_file.get(rel_path)
        if stored and stored[0] == current_hash:
            all_embedded.extend(stored[1])
            skipped += 1
            continue
        file_chunks = split_file(file)
        if not file_chunks:
            continue
        embedded = embed_chunks(file_chunks)
        for ec in embedded:
            ec.file_hash = current_hash
        all_embedded.extend(embedded)
        changed += 1

    print(f"{skipped} files unchanged (skipped), {changed} files re-embedded")
    print(f"{len(all_embedded)} chunks total")
    print()

    print("Storing index...")
    index_repository(repo_path, all_embedded)
    print()
    print("Ingestion complete")


def cmd_ask(args: argparse.Namespace) -> None:
    repo_path = Path(args.path).resolve()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    print("Retrieving relevant chunks...")
    retrieved_chunks = retrieve(args.question, repo_path, k=RERANK_CANDIDATES)

    if not retrieved_chunks:
        print()
        print("No index found for this repository.")
        print(f"Run `repollama ingest {repo_path}` first, then try again.")
        return

    print(f"Reranking {len(retrieved_chunks)} candidates...")
    for i, retrieved in enumerate(retrieved_chunks, start=1):
        print(f"  [{i}/{len(retrieved_chunks)}]", end="\r", flush=True)
        retrieved.rerank_score = score_chunk(args.question, retrieved)
    print()
    retrieved_chunks.sort(
        key=lambda rc: rc.rerank_score if rc.rerank_score is not None else 0.0,
        reverse=True,
    )
    # Drop chunks the judge scored 0 (unrelated), but keep at least one chunk
    # so the LLM still has context if every candidate scored low.
    relevant = [rc for rc in retrieved_chunks if (rc.rerank_score or 0.0) > 0.0]
    retrieved_chunks = (relevant or retrieved_chunks[:1])[:DEFAULT_TOP_K]

    for item in retrieved_chunks:
        chunk = item.embedded_chunk.chunk
        rerank = item.rerank_score if item.rerank_score is not None else 0.0
        print(
            f"[rerank={rerank:.2f} retrieve={item.score:.3f}] "
            f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
        )
        if args.verbose:
            print(preview_text(chunk.text))
            print("-" * 60)

    print("Building prompt...")
    system, prompt = build_prompt(args.question, retrieved_chunks)

    print("Querying LLM...")
    answer = ask_llm(system, prompt)

    print()
    print(answer)


# ══════════════════════════════════════════════════════


def main() -> None:
    args = parse_args()
    try:
        args.func(args)
    except RepoLlamaError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
