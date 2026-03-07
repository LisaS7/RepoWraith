from argparse import Namespace

from repowraith.cli import cmd_survey, parse_args
from tests.helpers import create_test_repo

# ═════════════════ COMMAND FUNCTIONS ══════════════════


def test_survey_non_verbose(tmp_path, capsys):
    create_test_repo(tmp_path)

    args = Namespace(path=tmp_path, verbose=False)

    cmd_survey(args)

    captured = capsys.readouterr()

    assert "3 files discovered" in captured.out
    assert "folder/file1.py" not in captured.out


def test_survey_verbose(tmp_path, capsys):
    create_test_repo(tmp_path)

    args = Namespace(path=tmp_path, verbose=True)

    cmd_survey(args)

    captured = capsys.readouterr()

    assert "3 files discovered" in captured.out
    assert "folder/file1.py" in captured.out


# ══════════════════════════════════════════════════════


def test_parse_args():
    args = parse_args(["survey", ".", "--verbose"])
    assert args.command == "survey"
    assert args.path == "."
    assert args.verbose is True
