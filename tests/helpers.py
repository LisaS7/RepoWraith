from pathlib import Path


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

    # Ignored suffix directory (*.egg-info) with a file inside it
    egg = tmp_path / "repowraith.egg-info"
    egg.mkdir()
    (egg / "PKG-INFO").write_text("Hello!", encoding="utf-8")

    # Ignored extension file in a normal location
    (tmp_path / "debug.log").write_text("Hello!", encoding="utf-8")
