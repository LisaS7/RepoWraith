import tempfile
from pathlib import Path

from repowraith.embed import embed_chunks
from repowraith.llm import ask_llm
from repowraith.prompt import build_prompt
from repowraith.retrieve import retrieve
from repowraith.splitter import split_repository
from repowraith.store import get_connection, index_repository
from repowraith.survey import survey_repository

with tempfile.TemporaryDirectory() as tmp_dir:
    repo_path = Path(tmp_dir)

    (repo_path / "README.md").write_text(
        "# Test repo\nThis project demonstrates indexing.\n",
        encoding="utf-8",
    )
    (repo_path / "app.py").write_text(
        "def main():\n    print('hello world')\n",
        encoding="utf-8",
    )
    (repo_path / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )

    files = survey_repository(repo_path)
    print(f"Files discovered: {len(files)}")

    chunks = split_repository(files)
    print(f"Chunks created: {len(chunks)}")

    embedded_chunks = embed_chunks(chunks)
    print(f"Embedded chunks: {len(embedded_chunks)}")

    index_repository(repo_path, embedded_chunks)
    print("Indexing complete.")

    with get_connection(repo_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM repositories")
        print("Repositories:", [dict(row) for row in cursor.fetchall()])

        cursor.execute("SELECT COUNT(*) FROM chunks")
        print("Chunk count:", cursor.fetchone()[0])

    retrieved_chunks = retrieve("Where is the hello world code?", repo_path, k=3)

    prompt = build_prompt(
        "Where is hello world printed?",
        retrieved_chunks,
        k=3,
    )

    print("\n--- PROMPT BUILT ---\n")
    print(prompt)

    answer = ask_llm(prompt)

    print("\n--- ANSWER ---\n")
    print(answer)
