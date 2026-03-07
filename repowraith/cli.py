import argparse

from repowraith.survey import survey_repository


def parse_args():
    parser = argparse.ArgumentParser(prog="repowraith")
    subparsers = parser.add_subparsers(dest="command")
    survey_parser = subparsers.add_parser("survey")
    survey_parser.add_argument("path")
    survey_parser.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == "survey":
        files = survey_repository(args.path)

        print(f"{len(files)} files discovered")

        if args.verbose:
            for file in files:
                print(file.as_posix())


if __name__ == "__main__":
    main()
