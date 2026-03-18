import requests

API_URL = "http://localhost:11434/api/generate"


def ask_llm(prompt: str) -> str:
    request_body = {"model": "llama3", "prompt": prompt, "stream": False}
    response = requests.post(API_URL, json=request_body)
    response.raise_for_status()
    return response.json()["response"]
