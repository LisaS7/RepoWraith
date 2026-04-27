import requests
from unittest.mock import Mock, patch

import pytest

from repollama.errors import OllamaConnectionError, OllamaResponseError
from repollama.ollama import post_to_ollama


@patch("repollama.ollama.requests.post")
def test_post_to_ollama_returns_parsed_json_on_success(mock_post) -> None:
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"embeddings": [[0.1, 0.2]]}
    mock_post.return_value = mock_response

    result = post_to_ollama("http://localhost:11434/api/embed", {"model": "m", "input": "hi"}, context="embed")

    assert result == {"embeddings": [[0.1, 0.2]]}


@patch("repollama.ollama.requests.post")
def test_post_to_ollama_raises_connection_error_on_timeout(mock_post) -> None:
    mock_post.side_effect = requests.Timeout()

    with pytest.raises(OllamaConnectionError, match="Timed out"):
        post_to_ollama("http://localhost:11434/api/embed", {}, context="embed")


@patch("repollama.ollama.requests.post")
def test_post_to_ollama_raises_connection_error_on_connection_error(mock_post) -> None:
    mock_post.side_effect = requests.ConnectionError()

    with pytest.raises(OllamaConnectionError, match="Could not connect"):
        post_to_ollama("http://localhost:11434/api/embed", {}, context="embed")


@patch("repollama.ollama.requests.post")
def test_post_to_ollama_raises_connection_error_on_request_exception(mock_post) -> None:
    mock_post.side_effect = requests.RequestException("upstream error")

    with pytest.raises(OllamaConnectionError, match="request failed"):
        post_to_ollama("http://localhost:11434/api/embed", {}, context="embed")


@patch("repollama.ollama.requests.post")
def test_post_to_ollama_raises_response_error_on_invalid_json(mock_post) -> None:
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("no json")
    mock_post.return_value = mock_response

    with pytest.raises(OllamaResponseError, match="invalid JSON"):
        post_to_ollama("http://localhost:11434/api/embed", {}, context="embed")
