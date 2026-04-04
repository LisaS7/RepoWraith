CREATE_REPOSITORIES_TABLE = """
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY,
    root_path TEXT NOT NULL UNIQUE,
    indexed_at TEXT NOT NULL
)
"""

CREATE_CHUNKS_TABLE = """
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding TEXT NOT NULL,
    file_hash TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
)
"""

MIGRATE_ADD_FILE_HASH = """
ALTER TABLE chunks ADD COLUMN file_hash TEXT NOT NULL DEFAULT ''
"""

CREATE_CHUNKS_REPO_INDEX = """
CREATE INDEX IF NOT EXISTS idx_chunks_repo_id
ON chunks(repo_id)
"""
