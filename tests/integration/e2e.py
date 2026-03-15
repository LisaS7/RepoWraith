import sqlite3
from pathlib import Path

from repowraith.embed import embed_chunks
from repowraith.splitter import split_repository
from repowraith.store import index_repository
from repowraith.survey import survey_repository

repo_path = Path(".")

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

conn = sqlite3.connect(".repowraith/index.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM repositories")
print(cursor.fetchall())
