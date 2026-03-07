from pathlib import Path

from repowraith.survey import survey_repository
from tests.helpers import create_test_repo


def test_survey_repository_ignores_paths(tmp_path: Path) -> None:
    create_test_repo(tmp_path)
    files = survey_repository(tmp_path)

    # Convert to strings for easy comparison
    stringy_paths = [p.as_posix() for p in files]

    # Expected files are present
    assert "README.md" in stringy_paths
    assert "folder/file1.py" in stringy_paths
    assert "folder/file2.html" in stringy_paths

    # Ignored dir contents are NOT present
    assert not any(s.startswith(".venv/") for s in stringy_paths)

    # Ignored suffix dir contents are NOT present
    assert not any(".egg-info/" in s for s in stringy_paths)

    # Ignored extension files are NOT present
    assert "debug.log" not in stringy_paths

    # All is in order
    assert stringy_paths == sorted(stringy_paths)
