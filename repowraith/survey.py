from pathlib import Path
from typing import Iterable

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "repowraith.egg-info",
}


def survey_repository(
    repo_root: Path, ignore_dirs: Iterable[str] = DEFAULT_IGNORE_DIRS
):
    """
    Walk a repository and return an ordered list of files.

    - `files` are returned as Paths relative to repo_root.
    - Ignores directories by name (e.g. ".git", ".venv").
    """

    root = Path(repo_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repo root is not a directory: {root}")

    ignore = set(ignore_dirs)
    found = []
    print(ignore)

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # this breaks the path into parts and checks if any of them are in the ignore list
        rel = path.relative_to(root)
        ignore_dir = bool([part for part in rel.parts if part in ignore])

        if ignore_dir:
            continue

        found.append(rel)

    # Use as_posix so sorting behaves the same on different operating systems
    found.sort(key=lambda p: p.as_posix())
    return found


files = survey_repository(Path("/home/lisa/Documents/Projects/RepoWraith"))
print(files)
