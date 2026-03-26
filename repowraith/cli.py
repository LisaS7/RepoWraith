import argparse
from pathlib import Path

from repowraith.embed import embed_chunks
from repowraith.llm import ask_llm
from repowraith.prompt import build_prompt
from repowraith.retrieve import retrieve
from repowraith.splitter import split_repository
from repowraith.store import index_repository
from repowraith.survey import survey_repository


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
    full_paths = [repo_path / file for file in files]
    print(f"{len(files)} files discovered")

    print()

    print("Chunking files...")
    chunks = split_repository(full_paths)
    print(f"{len(chunks)} chunks created")

    print()

    print("Generating embeddings...")
    embedded_chunks = embed_chunks(chunks)
    print(f"{len(embedded_chunks)} chunks embedded")

    print()

    print("Storing index...")
    index_repository(repo_path, embedded_chunks)

    print()

    print("Ingestion complete")


def cmd_ask(args):
    repo_path = Path(args.path)

    print("Retrieving relevant chunks...")
    retrieved_chunks = retrieve(args.question, repo_path)

    for item in retrieved_chunks:
        chunk = item.embedded_chunk.chunk
        print(
            f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line} score={item.score}"
        )
        print(chunk.text)
        print("-" * 80)

    print("Building prompt...")
    prompt = build_prompt(args.question, retrieved_chunks)

    print("Querying LLM...")
    answer = ask_llm(prompt)

    print()
    print(answer)


# ══════════════════════════════════════════════════════


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
