import argparse
from pathlib import Path

from repowraith.embed import embed_chunks
from repowraith.splitter import split_repository
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
    ingest_parser.add_argument(
        "--verbose", action="store_true", help="Print discovered file paths"
    )

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
    repo_path = Path(args.path)
    files = survey_repository(repo_path)
    chunks = split_repository(files)
    embedded_chunks = embed_chunks(chunks)
    print(f"{len(embedded_chunks)} chunks embedded")


# ══════════════════════════════════════════════════════


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
