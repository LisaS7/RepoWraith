import logging
import re

from repollama.config import GENERATE_TIMEOUT_SECONDS, OLLAMA_CHAT_URL, RERANK_MODEL
from repollama.errors import OllamaResponseError
from repollama.models import RetrievedChunk
from repollama.ollama import post_to_ollama

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a relevance judge for a code search system. "
    "Given a user question and a single excerpt from a source file or document, "
    "output one integer from 0 to 10 indicating how directly the excerpt helps "
    "answer the question. "
    "10 = the excerpt directly answers the question. "
    "5 = the excerpt is on-topic but does not answer it. "
    "0 = the excerpt is unrelated. "
    "Output only the integer. No words, no punctuation, no explanation."
)

_USER_TEMPLATE = (
    "Question:\n{question}\n\n"
    "Excerpt from {file_path}:{start_line}-{end_line}:\n{text}\n\n"
    "Relevance score (0-10):"
)

# Match an integer 0–10 surrounded by word boundaries. Tries "10" first so that
# "10/10" parses as 10 rather than 1.
_SCORE_RE = re.compile(r"\b(10|[0-9])\b")


def score_chunk(question: str, retrieved: RetrievedChunk) -> float:
    chunk = retrieved.chunk
    user_prompt = _USER_TEMPLATE.format(
        question=question,
        file_path=chunk.file_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        text=chunk.text,
    )
    body = {
        "model": RERANK_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 8},
    }
    response_json = post_to_ollama(
        OLLAMA_CHAT_URL,
        body,
        context="rerank",
        timeout=GENERATE_TIMEOUT_SECONDS,
    )

    message = response_json.get("message", {})
    text = message.get("content") if isinstance(message, dict) else None

    if not isinstance(text, str):
        raise OllamaResponseError(
            "Ollama rerank response missing 'message.content' field."
        )

    match = _SCORE_RE.search(text)
    if not match:
        logger.debug("Could not parse rerank score from response: %r", text)
        return 0.0

    return int(match.group(1)) / 10.0


def rerank_chunks(
    question: str,
    retrieved_chunks: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    for retrieved in retrieved_chunks:
        retrieved.rerank_score = score_chunk(question, retrieved)

    retrieved_chunks.sort(
        key=lambda rc: rc.rerank_score if rc.rerank_score is not None else 0.0,
        reverse=True,
    )
    return retrieved_chunks
