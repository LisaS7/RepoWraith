from argparse import Namespace
from pathlib import Path

import pytest

from repollama.cli import cmd_ask, cmd_ingest, cmd_survey, main, parse_args
from repollama.errors import OllamaConnectionError
from repollama.models import Chunk, EmbeddedChunk, RetrievedChunk
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

    monkeypatch.setattr("repollama.cli.embed_chunks", fake_embed_chunks)
    monkeypatch.setattr("repollama.cli.index_repository", fake_index_repository)

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
    monkeypatch.setattr("repollama.cli.retrieve", lambda question, repo_path, k: [])

    args = Namespace(path=str(tmp_path), question="what does this do", verbose=False)
    cmd_ask(args)

    captured = capsys.readouterr()
    assert "No index found" in captured.out


def test_cmd_ask_prints_answer_on_success(tmp_path, capsys, monkeypatch):
    retrieved = [_make_retrieved_chunk("repollama/store.py")]

    monkeypatch.setattr("repollama.cli.retrieve", lambda question, repo_path, k: retrieved)
    monkeypatch.setattr("repollama.cli.score_chunk", lambda question, retrieved: 0.9)
    monkeypatch.setattr("repollama.cli.ask_llm", lambda system, prompt: "It uses SQLite.")

    args = Namespace(path=str(tmp_path), question="how is data stored", verbose=False)
    cmd_ask(args)

    captured = capsys.readouterr()
    assert "It uses SQLite." in captured.out


def test_cmd_ask_verbose_prints_chunk_preview(tmp_path, capsys, monkeypatch):
    retrieved = [_make_retrieved_chunk("repollama/store.py", text="def insert(): pass")]

    monkeypatch.setattr("repollama.cli.retrieve", lambda question, repo_path, k: retrieved)
    monkeypatch.setattr("repollama.cli.score_chunk", lambda question, retrieved: 0.9)
    monkeypatch.setattr("repollama.cli.ask_llm", lambda system, prompt: "answer")

    args = Namespace(path=str(tmp_path), question="how is data stored", verbose=True)
    cmd_ask(args)

    captured = capsys.readouterr()
    assert "def insert(): pass" in captured.out


def test_ingest_excludes_deleted_file_chunks(tmp_path, monkeypatch):
    create_test_repo(tmp_path)

    deleted_file = "folder/file1.py"
    surviving_file = "folder/file2.py"

    fake_chunk = Chunk(file_path=tmp_path / surviving_file, start_line=1, end_line=5, text="x")
    deleted_chunk = Chunk(file_path=tmp_path / deleted_file, start_line=1, end_line=5, text="deleted")

    surviving_ec = EmbeddedChunk(chunk=fake_chunk, embedding=[0.1, 0.2], file_hash="abc")
    deleted_ec = EmbeddedChunk(chunk=deleted_chunk, embedding=[0.3, 0.4], file_hash="old")

    # Simulate DB that still has chunks for a deleted file
    fake_existing = {
        surviving_file: ("abc", [surviving_ec]),
        deleted_file: ("old", [deleted_ec]),
    }

    stored = {}

    monkeypatch.setattr("repollama.cli.load_chunks_by_file", lambda *_: fake_existing)
    monkeypatch.setattr("repollama.cli.hash_file", lambda f: "abc")
    monkeypatch.setattr("repollama.cli.split_file", lambda f: [])
    monkeypatch.setattr("repollama.cli.embed_chunks", lambda chunks: [])
    monkeypatch.setattr("repollama.cli.index_repository", lambda repo_path, chunks: stored.update({"chunks": chunks}))

    args = Namespace(path=tmp_path)
    cmd_ingest(args)

    stored_paths = {ec.chunk.file_path.relative_to(tmp_path).as_posix() for ec in stored["chunks"]}
    assert deleted_file not in stored_paths


def test_main_exits_with_code_1_on_repollama_error(monkeypatch, capsys):
    def raise_error(args):
        raise OllamaConnectionError("no ollama running")

    monkeypatch.setattr("repollama.cli.parse_args", lambda: Namespace(func=raise_error))

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "no ollama running" in capsys.readouterr().err
