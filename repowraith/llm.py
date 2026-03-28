import requests

from repowraith.config import LLM_MODEL, OLLAMA_GENERATE_URL

REQUEST_TIMEOUT_SECONDS = 30


class OllamaError(RuntimeError):
    """Base error for Ollama API failures."""


class OllamaConnectionError(OllamaError):
    """Raised when Ollama cannot be reached."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an unexpected response."""


def ask_llm(prompt: str) -> str:
    request_body = {"model": LLM_MODEL, "prompt": prompt, "stream": False}

    try:
        response = requests.post(
            OLLAMA_GENERATE_URL, json=request_body, timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise OllamaConnectionError(
            f"Timed out waiting for Ollama generation response from "
            f"{OLLAMA_GENERATE_URL} using model '{LLM_MODEL}'."
        ) from exc
    except requests.ConnectionError as exc:
        raise OllamaConnectionError(
            f"Could not connect to Ollama at {OLLAMA_GENERATE_URL}. "
            f"Is Ollama running?"
        ) from exc
    except requests.RequestException as exc:
        raise OllamaConnectionError(f"Ollama generate request failed: {exc}") from exc

    try:
        response_json = response.json()
    except ValueError as exc:
        raise OllamaResponseError(
            "Ollama returned invalid JSON for generate request."
        ) from exc

    answer = response_json.get("response")

    if not isinstance(answer, str) or not answer.strip():
        raise OllamaResponseError("Ollama response missing non-empty 'response' field.")

    return answer
