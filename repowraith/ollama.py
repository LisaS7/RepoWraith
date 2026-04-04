import requests

from repowraith.config import REQUEST_TIMEOUT_SECONDS
from repowraith.errors import OllamaConnectionError, OllamaResponseError


def post_to_ollama(url: str, body: dict, context: str, timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict:
    try:
        response = requests.post(url, json=body, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise OllamaConnectionError(
            f"Timed out waiting for Ollama {context} response from {url}."
        ) from exc
    except requests.ConnectionError as exc:
        raise OllamaConnectionError(
            f"Could not connect to Ollama at {url}. Is Ollama running?"
        ) from exc
    except requests.RequestException as exc:
        raise OllamaConnectionError(
            f"Ollama {context} request failed: {exc}"
        ) from exc

    try:
        return response.json()
    except ValueError as exc:
        raise OllamaResponseError(
            f"Ollama returned invalid JSON for {context} request."
        ) from exc
