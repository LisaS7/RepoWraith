from argparse import Namespace

from repowraith.cli import cmd_ingest, cmd_survey, parse_args
from tests.helpers import create_test_file, create_test_repo

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


def test_ingest(tmp_path, capsys, monkeypatch):
    create_test_repo(tmp_path)
    create_test_file(tmp_path, "test_file.txt", 50)

    args = Namespace(path=tmp_path)

    def fake_embed_chunks(chunks):
        return ["fake1", "fake2"]

    stored = {}

    def fake_index_repository(repo_path, embedded_chunks):
        stored["repo_path"] = repo_path
        stored["embedded_chunks"] = embedded_chunks

    monkeypatch.setattr("repowraith.cli.embed_chunks", fake_embed_chunks)
    monkeypatch.setattr("repowraith.cli.index_repository", fake_index_repository)

    cmd_ingest(args)

    captured = capsys.readouterr()

    assert "Surveying repository..." in captured.out
    assert "Chunking files..." in captured.out
    assert "Generating embeddings..." in captured.out
    assert "Storing index..." in captured.out
    assert "Ingestion complete" in captured.out

    assert stored["repo_path"] == tmp_path
    assert stored["embedded_chunks"] == ["fake1", "fake2"]


# ═════════════════ PARSEARGS ══════════════════


def test_parse_args_survey():
    args = parse_args(["survey", ".", "--verbose"])
    assert args.command == "survey"
    assert args.path == "."
    assert args.verbose is True


def test_parse_args_ingest():
    args = parse_args(["ingest", "."])
    assert args.command == "ingest"
    assert args.path == "."
