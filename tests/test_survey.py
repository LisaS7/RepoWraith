from pathlib import Path

from repowraith.survey import survey_repository


def create_test_repo(tmp_path: Path) -> None:

    # Repo root files
    (tmp_path / "README.md").write_text("Hello!", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("Hello!", encoding="utf-8")

    # Normal subfolder with files
    test_dir = tmp_path / "folder"
    test_dir.mkdir()
    (test_dir / "file1.py").write_text("Hello!", encoding="utf-8")
    (test_dir / "file2.html").write_text("Hello!", encoding="utf-8")

    # Ignored directory with a file inside it
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("Hello!", encoding="utf-8")


def test_survey_repository_ignores_paths(tmp_path: Path) -> None:
    create_test_repo(tmp_path)
    files = survey_repository(tmp_path)

    # Convert to strings for easy comparison
    stringy_paths = [p.as_posix() for p in files]

    # Expected files are present
    assert "README.md" in stringy_paths
    assert ".gitignore" in stringy_paths
    assert "folder/file1.py" in stringy_paths
    assert "folder/file2.html" in stringy_paths

    # Ignored dir contents are NOT present
    assert not any(s.startswith(".venv/") for s in stringy_paths)

    # All is in order
    assert stringy_paths == sorted(stringy_paths)
