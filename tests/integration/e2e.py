import tempfile
from pathlib import Path

from repowraith.embed import embed_chunks
from repowraith.splitter import split_repository
from repowraith.store import get_connection, index_repository
from repowraith.survey import survey_repository

with tempfile.TemporaryDirectory() as tmp_dir:
    repo_path = Path(tmp_dir)

    (repo_path / "README.md").write_text("# Test repo\n", encoding="utf-8")
    (repo_path / "app.py").write_text("print('hello world')\n", encoding="utf-8")

    files = survey_repository(repo_path)
    print(f"Files discovered: {len(files)}")

    chunks = split_repository(files)
    print(f"Chunks created: {len(chunks)}")

    embedded_chunks = embed_chunks(chunks)
    print(f"Embedded chunks: {len(embedded_chunks)}")

    if embedded_chunks:
        first = embedded_chunks[0]
        print(f"First chunk file: {first.chunk.file_path}")
        print(f"First chunk lines: {first.chunk.start_line}-{first.chunk.end_line}")
        print(f"Embedding length: {len(first.embedding)}")

    index_repository(repo_path, embedded_chunks)
    print("Indexing complete.")

    with get_connection(repo_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM repositories")
        print("Repositories:", cursor.fetchall())

        cursor.execute("SELECT COUNT(*) FROM chunks")
        print("Chunk count:", cursor.fetchone()[0])
