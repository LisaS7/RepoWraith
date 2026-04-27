import logging
from pathlib import Path

from repollama.config import DEFAULT_TOP_K
from repollama.models import RetrievedChunk

_TEMPLATE = (Path(__file__).parent / "prompt_template.txt").read_text(encoding="utf-8")
_SYSTEM_PROMPT = (Path(__file__).parent / "system_prompt.txt").read_text(encoding="utf-8").strip()


def format_chunk(retrieved_chunk: RetrievedChunk, index: int) -> str:
    chunk = retrieved_chunk.embedded_chunk.chunk
    header = f"--- [{index}] {chunk.file_path}:{chunk.start_line}-{chunk.end_line} ---"
    chunky_string = f"{header}\n{chunk.text}"
    return chunky_string


def build_prompt(
    question: str,
    retrieved_chunks: list[RetrievedChunk],
    k: int = DEFAULT_TOP_K,
) -> tuple[str, str]:
    top_chunks = retrieved_chunks[0:k]
    formatted_chunks = []
    for index, retrieved_chunk in enumerate(top_chunks, start=1):
        chunk_str = format_chunk(retrieved_chunk, index)
        formatted_chunks.append(chunk_str)

    context_text = "\n\n".join(formatted_chunks)
    user_prompt = _TEMPLATE.format(question=question, context=context_text)

    logger = logging.getLogger(__name__)
    logger.debug("Prompt: %d chunks, %d chars", len(top_chunks), len(user_prompt))

    return _SYSTEM_PROMPT, user_prompt
