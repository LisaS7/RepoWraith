from repowraith.config import LLM_MODEL, OLLAMA_GENERATE_URL
from repowraith.errors import OllamaResponseError
from repowraith.ollama import post_to_ollama


def ask_llm(prompt: str) -> str:
    request_body = {"model": LLM_MODEL, "prompt": prompt, "stream": False}
    response_json = post_to_ollama(OLLAMA_GENERATE_URL, request_body, context="generate")

    answer = response_json.get("response")

    if not isinstance(answer, str) or not answer.strip():
        raise OllamaResponseError("Ollama response missing non-empty 'response' field.")

    return answer
