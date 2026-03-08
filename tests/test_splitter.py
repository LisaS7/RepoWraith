from repowraith.splitter import CHUNK_SIZE, OVERLAP, Chunk, split_file
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
