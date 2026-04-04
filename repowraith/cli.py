import argparse
import logging
import sys
from pathlib import Path

from repowraith.embed import embed_chunks
from repowraith.errors import RepoWraithError
from repowraith.llm import ask_llm
from repowraith.prompt import build_prompt
from repowraith.retrieve import retrieve
from repowraith.splitter import hash_file, split_file
from repowraith.store import (
    get_connection,
    get_repo_id,
    index_repository,
    init_db,
    load_chunks_by_file,
)
from repowraith.survey import survey_repository


def preview_text(text: str, max_lines: int = 5) -> str:
    lines = text.strip().splitlines()
    preview = lines[:max_lines]

    if len(lines) > max_lines:
        preview.append("...")

    return "\n".join(preview)


def parse_args(args=None):
    parser = argparse.ArgumentParser(prog="repowraith")
    subparsers = parser.add_subparsers(dest="command", required=True)

    survey_parser = subparsers.add_parser(
        "survey", help="Survey a repository and list indexable files"
    )
    survey_parser.add_argument("path", help="Path to the repository root")
    survey_parser.add_argument(
        "--verbose", action="store_true", help="Print discovered file paths"
    )

    ingest_parser = subparsers.add_parser(
        "ingest", help="Index a repository so it can be queried using RepoWraith"
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


def cmd_survey(args):
    files = survey_repository(Path(args.path))

    print(f"{len(files)} files discovered")

    if args.verbose:
        print()
        for file in files:
            print(file.as_posix())


def cmd_ingest(args):
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

    for file in files:
        rel_path = file.relative_to(repo_path).as_posix()
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


def cmd_ask(args):
    repo_path = Path(args.path).resolve()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    print("Retrieving relevant chunks...")
    retrieved_chunks = retrieve(args.question, repo_path)

    if not retrieved_chunks:
        print()
        print("No index found for this repository.")
        print(f"Run `repowraith ingest {repo_path}` first, then try again.")
        return

    for item in retrieved_chunks:
        chunk = item.embedded_chunk.chunk
        print(
            f"[score={item.score:.3f}] {chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
        )
        if args.verbose:
            print(preview_text(chunk.text))
            print("-" * 60)

    print("Building prompt...")
    prompt = build_prompt(args.question, retrieved_chunks)

    print("Querying LLM...")
    answer = ask_llm(prompt)

    print()
    print(answer)


# ══════════════════════════════════════════════════════


def main():
    args = parse_args()
    try:
        args.func(args)
    except RepoWraithError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
