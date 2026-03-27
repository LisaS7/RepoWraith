import requests

from repowraith.config import LLM_MODEL, OLLAMA_GENERATE_URL


def ask_llm(prompt: str) -> str:
    request_body = {"model": LLM_MODEL, "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_GENERATE_URL, json=request_body)
    response.raise_for_status()
    return response.json()["response"]
