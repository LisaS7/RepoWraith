from unittest.mock import Mock, patch

import pytest

from repowraith.config import GENERATE_TIMEOUT_SECONDS, LLM_MAX_TOKENS, LLM_MODEL, LLM_TEMPERATURE, OLLAMA_CHAT_URL
from repowraith.errors import OllamaResponseError
from repowraith.llm import ask_llm

SYSTEM = "You are a code assistant."
PROMPT = "Where is the hello world code?"
CHAT_RESPONSE = {"message": {"role": "assistant", "content": "The hello world code is in app.py."}}


@patch("repowraith.ollama.requests.post")
def test_ask_llm_sends_expected_request(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = CHAT_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    ask_llm(SYSTEM, PROMPT)

    mock_post.assert_called_once_with(
        OLLAMA_CHAT_URL,
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": PROMPT},
            ],
            "stream": False,
            "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_MAX_TOKENS},
        },
        timeout=GENERATE_TIMEOUT_SECONDS,
    )


@patch("repowraith.ollama.requests.post")
def test_ask_llm_returns_response_text(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = CHAT_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = ask_llm(SYSTEM, PROMPT)

    assert result == "The hello world code is in app.py."


@patch("repowraith.ollama.requests.post")
def test_ask_llm_raises_when_response_field_is_absent(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with pytest.raises(OllamaResponseError, match="missing non-empty 'message.content'"):
        ask_llm(SYSTEM, "What does this do?")


@patch("repowraith.ollama.requests.post")
def test_ask_llm_raises_when_response_field_is_empty_string(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"message": {"role": "assistant", "content": "   "}}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with pytest.raises(OllamaResponseError, match="missing non-empty 'message.content'"):
        ask_llm(SYSTEM, "What does this do?")


@patch("repowraith.ollama.requests.post")
def test_ask_llm_raises_when_response_field_is_not_a_string(mock_post):
    mock_response = Mock()
    mock_response.json.return_value = {"message": {"role": "assistant", "content": 42}}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    with pytest.raises(OllamaResponseError, match="missing non-empty 'message.content'"):
        ask_llm(SYSTEM, "What does this do?")
