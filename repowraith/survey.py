from pathlib import Path
from typing import Iterable

from repowraith.config import (
    DEFAULT_IGNORE_DIR_SUFFIXES,
    DEFAULT_IGNORE_DIRS,
    DEFAULT_IGNORE_EXTENSIONS,
    DEFAULT_IGNORE_FILENAMES,
)


def survey_repository(
    repo_root: Path,
    ignore_dirs: Iterable[str] = DEFAULT_IGNORE_DIRS,
    ignore_dir_suffixes: Iterable[str] = DEFAULT_IGNORE_DIR_SUFFIXES,
    ignore_extensions: Iterable[str] = DEFAULT_IGNORE_EXTENSIONS,
    ignore_filenames: Iterable[str] = DEFAULT_IGNORE_FILENAMES,
) -> list[Path]:
    """
    Walk a repository and return an ordered list of files.

    - Returns absolute file paths
    - Ignores junk directories
    - Ignores junk file extensions and filenames
    """

    root = Path(repo_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repo root is not a directory: {root}")

    ignore_dirs = set(ignore_dirs)
    ignore_dir_suffixes = set(ignore_dir_suffixes)
    ignore_extensions = set(ignore_extensions)
    ignore_filenames = set(ignore_filenames)
    found = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in ignore_extensions or path.name in ignore_extensions or path.name in ignore_filenames:
            continue

        # break the path into parts and checks if any of them are in the ignore lists
        rel = path.relative_to(root)
        ignore_dir = False

        for part in rel.parts:
            if part in ignore_dirs:
                ignore_dir = True
                break

            for suffix in ignore_dir_suffixes:
                if part.endswith(suffix):
                    ignore_dir = True
                    break

            if ignore_dir:
                break

        if ignore_dir:
            continue

        found.append(path)

    # Use as_posix so sorting behaves the same on different operating systems
    found.sort(key=lambda p: p.as_posix())
    return found
