from pathlib import Path

import pytest

from repowraith.survey import survey_repository
from tests.helpers import create_test_repo


def test_survey_repository_ignores_paths(tmp_path: Path) -> None:
    create_test_repo(tmp_path)
    files = survey_repository(tmp_path)

    # Convert to strings for easy comparison
    stringy_paths = [p.as_posix() for p in files]

    # Expected files are present
    assert tmp_path / "README.md" in files
    assert tmp_path / "folder/file1.py" in files
    assert tmp_path / "folder/file2.html" in files

    # Ignored dir contents are NOT present
    assert not any("/.venv/" in s for s in stringy_paths)

    # Ignored suffix dir contents are NOT present
    assert not any(".egg-info/" in s for s in stringy_paths)

    # Ignored extension files are NOT present
    assert not any(
        s.endswith("/debug.log") or s.endswith("debug.log") for s in stringy_paths
    )

    # All is in order
    assert stringy_paths == sorted(stringy_paths)


def test_survey_raises_for_nonexistent_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        survey_repository(tmp_path / "does_not_exist")


def test_survey_raises_for_non_directory(tmp_path: Path) -> None:
    file = tmp_path / "some_file.txt"
    file.write_text("content", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        survey_repository(file)
