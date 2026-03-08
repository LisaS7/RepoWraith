from repowraith.splitter import CHUNK_SIZE, OVERLAP, Chunk, split_file, split_repository
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
