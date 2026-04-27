from unittest.mock import patch

from repollama.models import Chunk
from repollama.splitter import CHUNK_SIZE, OVERLAP, split_file, split_repository
from tests.helpers import create_test_file


def test_split_file(tmp_path):
    total_lines = 450
    test_file = create_test_file(tmp_path, "file.txt", total_lines)

    chunks = split_file(test_file)
    assert isinstance(chunks[0], Chunk)
    assert isinstance(chunks[0].text, str)
    assert chunks[0].file_path == test_file
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == CHUNK_SIZE
    assert chunks[1].start_line == CHUNK_SIZE - OVERLAP + 1
    assert chunks[-1].end_line == total_lines


def test_split_repository(tmp_path):
    file1 = create_test_file(tmp_path, "file1.txt", 10)
    file2 = create_test_file(tmp_path, "file2.txt", 450)

    chunks = split_repository([file1, file2])

    assert all(isinstance(chunk, Chunk) for chunk in chunks)

    file_paths = {chunk.file_path for chunk in chunks}
    assert file1 in file_paths
    assert file2 in file_paths

    expected_count = len(split_file(file1)) + len(split_file(file2))
    assert len(chunks) == expected_count


def test_split_file_shorter_than_chunk_size_produces_single_chunk(tmp_path):
    total_lines = 10
    test_file = create_test_file(tmp_path, "short.txt", total_lines)

    chunks = split_file(test_file)

    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == total_lines


def test_split_file_falls_back_to_latin1_for_non_utf8_content(tmp_path):
    file_path = tmp_path / "latin1.py"
    # 'é' encoded as latin-1 is 0xe9, which is invalid UTF-8
    file_path.write_bytes("caf\xe9\n".encode("latin-1"))

    chunks = split_file(file_path)

    assert len(chunks) == 1
    assert "café" in chunks[0].text


def test_split_file_returns_empty_list_when_all_encodings_fail(tmp_path):
    file_path = tmp_path / "bad.py"
    file_path.write_bytes(b"content")

    side_effects = [
        UnicodeDecodeError("utf-8", b"", 0, 1, "invalid byte"),
        OSError("permission denied"),
    ]

    with patch("repollama.splitter.Path.read_text", side_effect=side_effects):
        chunks = split_file(file_path)

    assert chunks == []
