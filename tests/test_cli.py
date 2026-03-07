# TODO:
# Call cmd_survey
# Output contains N files discovered
# Output does not contain file paths

# Call verbose
# Output still contains count
# output contains expected paths

# how to test parse_args ......?

from argparse import Namespace

from repowraith.cli import cmd_survey


def test_survey_non_verbose(capsys):
    args = Namespace(path=".", verbose=False)

    cmd_survey(args)

    captured = capsys.readouterr()

    assert "files discovered" in captured.out


def test_survey_verbose(capsys):
    args = Namespace(path=".", verbose=True)

    cmd_survey(args)

    captured = capsys.readouterr()
    print(captured)

    assert "files discovered" in captured.out
    assert "repowraith/" in captured.out
