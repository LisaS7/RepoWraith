from pathlib import Path

from repowraith.models import RetrievedChunk


def format_chunk(retrieved_chunk: RetrievedChunk, index: int) -> str:
    chunk = retrieved_chunk.embedded_chunk.chunk
    chunky_string = (
        f"[{index}] {chunk.file_path}:{chunk.start_line}-{chunk.end_line}\n{chunk.text}"
    )
    return chunky_string


def build_prompt(
    question: str,
    retrieved_chunks: list[RetrievedChunk],
    k: int = 5,
    verbose: bool = False,
) -> str:
    top_chunks = retrieved_chunks[0:k]
    formatted_chunks = []
    for index, retrieved_chunk in enumerate(top_chunks, start=1):
        chunk_str = format_chunk(retrieved_chunk, index)
        formatted_chunks.append(chunk_str)

    template_path = Path(__file__).parent / "prompt_template.txt"
    template_text = template_path.read_text(encoding="utf-8")

    context_text = "\n\n".join(formatted_chunks)
    prompt = template_text.format(question=question, context=context_text)

    if verbose:
        print("\n--- Prompt Debug ---")
        print(f"Question: {question}")
        print(f"Chunks used: {len(top_chunks)}")
        for i, chunk in enumerate(top_chunks, start=1):
            c = chunk.embedded_chunk.chunk
            print(f"[{i}] {c.file_path}:{c.start_line}-{c.end_line}")
        print(f"Prompt length: {len(prompt)} chars")
        print()

    return prompt
