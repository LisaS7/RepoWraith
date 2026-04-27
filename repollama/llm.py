import logging

from repollama.config import GENERATE_TIMEOUT_SECONDS, LLM_MAX_TOKENS, LLM_MODEL, LLM_TEMPERATURE, OLLAMA_CHAT_URL
from repollama.errors import OllamaResponseError
from repollama.ollama import post_to_ollama

logger = logging.getLogger(__name__)


def ask_llm(system: str, prompt: str) -> str:
    request_body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_MAX_TOKENS},
    }

    logger.debug("=== SYSTEM ===\n%s", system)
    logger.debug("=== PROMPT ===\n%s", prompt)

    response_json = post_to_ollama(OLLAMA_CHAT_URL, request_body, context="generate", timeout=GENERATE_TIMEOUT_SECONDS)

    message = response_json.get("message", {})
    answer = message.get("content") if isinstance(message, dict) else None

    logger.debug("=== RAW RESPONSE ===\n%r", answer)

    if not isinstance(answer, str) or not answer.strip():
        raise OllamaResponseError("Ollama chat response missing non-empty 'message.content' field.")

    return answer
