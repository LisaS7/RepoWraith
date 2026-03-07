import argparse
from pathlib import Path

from repowraith.survey import survey_repository


def parse_args():
    parser = argparse.ArgumentParser(prog="repowraith")
    subparsers = parser.add_subparsers(dest="command", required=True)

    survey_parser = subparsers.add_parser("survey")
    survey_parser.add_argument("path")
    survey_parser.add_argument("--verbose", action="store_true")

    # Register command functions
    survey_parser.set_defaults(func=cmd_survey)

    return parser.parse_args()


# ═════════════════ COMMAND FUNCTIONS ══════════════════


def cmd_survey(args):
    files = survey_repository(Path(args.path))

    print(f"{len(files)} files discovered")

    if args.verbose:
        for file in files:
            print(file.as_posix())


# ══════════════════════════════════════════════════════


def main():
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
