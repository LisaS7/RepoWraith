from unittest.mock import Mock, patch

from repowraith.config import OLLAMA_GENERATE_URL, REQUEST_TIMEOUT_SECONDS
from repowraith.llm import ask_llm


@patch("repowraith.ollama.requests.post")
def test_ask_llm_sends_expected_request(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"response": "hello from ollama"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    prompt = "Where is the hello world code?"
    ask_llm(prompt)

    mock_post.assert_called_once_with(
        OLLAMA_GENERATE_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


@patch("repowraith.ollama.requests.post")
def test_ask_llm_returns_response_text(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"response": "The hello world code is in app.py."}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = ask_llm("Where is the hello world code?")

    assert result == "The hello world code is in app.py."
