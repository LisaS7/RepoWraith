from repowraith.config import GENERATE_TIMEOUT_SECONDS, LLM_MAX_TOKENS, LLM_MODEL, LLM_TEMPERATURE, OLLAMA_GENERATE_URL
from repowraith.errors import OllamaResponseError
from repowraith.ollama import post_to_ollama


def ask_llm(prompt: str) -> str:
    request_body = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_MAX_TOKENS},
    }
    response_json = post_to_ollama(OLLAMA_GENERATE_URL, request_body, context="generate", timeout=GENERATE_TIMEOUT_SECONDS)

    answer = response_json.get("response")

    if not isinstance(answer, str) or not answer.strip():
        raise OllamaResponseError("Ollama response missing non-empty 'response' field.")

    return answer
