from argparse import Namespace
from pathlib import Path

import pytest

from repowraith.cli import cmd_ask, cmd_ingest, cmd_survey, main, parse_args
from repowraith.errors import OllamaConnectionError
from repowraith.models import Chunk, EmbeddedChunk, RetrievedChunk
from tests.helpers import create_test_file, create_test_repo


def _make_retrieved_chunk(file_path: str, text: str = "some code") -> RetrievedChunk:
    chunk = Chunk(file_path=Path(file_path), start_line=1, end_line=5, text=text)
    embedded = EmbeddedChunk(chunk=chunk, embedding=[0.1, 0.2])
    return RetrievedChunk(embedded_chunk=embedded, score=0.9)

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

    fake_chunk = Chunk(file_path=tmp_path / "test_file.txt", start_line=1, end_line=10, text="x")

    all_returned: list[EmbeddedChunk] = []

    def fake_embed_chunks(chunks):
        result = [EmbeddedChunk(chunk=fake_chunk, embedding=[0.1, 0.2]) for _ in chunks]
        all_returned.extend(result)
        return result

    stored = {}

    def fake_index_repository(repo_path, embedded_chunks):
        stored["repo_path"] = repo_path
        stored["embedded_chunks"] = embedded_chunks

    monkeypatch.setattr("repowraith.cli.embed_chunks", fake_embed_chunks)
    monkeypatch.setattr("repowraith.cli.index_repository", fake_index_repository)

    cmd_ingest(args)

    captured = capsys.readouterr()

    assert "Surveying repository..." in captured.out
    assert "Chunking and embedding files..." in captured.out
    assert "Storing index..." in captured.out
    assert "Ingestion complete" in captured.out

    assert stored["repo_path"] == tmp_path
    assert stored["embedded_chunks"] == all_returned


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


def test_cmd_ask_prints_no_index_message_when_retrieve_returns_empty(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("repowraith.cli.retrieve", lambda question, repo_path: [])

    args = Namespace(path=str(tmp_path), question="what does this do", verbose=False)
    cmd_ask(args)

    captured = capsys.readouterr()
    assert "No index found" in captured.out


def test_cmd_ask_prints_answer_on_success(tmp_path, capsys, monkeypatch):
    retrieved = [_make_retrieved_chunk("repowraith/store.py")]

    monkeypatch.setattr("repowraith.cli.retrieve", lambda question, repo_path: retrieved)
    monkeypatch.setattr("repowraith.cli.ask_llm", lambda prompt: "It uses SQLite.")

    args = Namespace(path=str(tmp_path), question="how is data stored", verbose=False)
    cmd_ask(args)

    captured = capsys.readouterr()
    assert "It uses SQLite." in captured.out


def test_cmd_ask_verbose_prints_chunk_preview(tmp_path, capsys, monkeypatch):
    retrieved = [_make_retrieved_chunk("repowraith/store.py", text="def insert(): pass")]

    monkeypatch.setattr("repowraith.cli.retrieve", lambda question, repo_path: retrieved)
    monkeypatch.setattr("repowraith.cli.ask_llm", lambda prompt: "answer")

    args = Namespace(path=str(tmp_path), question="how is data stored", verbose=True)
    cmd_ask(args)

    captured = capsys.readouterr()
    assert "def insert(): pass" in captured.out


def test_main_exits_with_code_1_on_repowraith_error(monkeypatch, capsys):
    def raise_error(args):
        raise OllamaConnectionError("no ollama running")

    monkeypatch.setattr("repowraith.cli.parse_args", lambda: Namespace(func=raise_error))

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "no ollama running" in capsys.readouterr().err
