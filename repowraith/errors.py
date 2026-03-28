class RepoWraithError(RuntimeError):
    """Base error for RepoWraith failures."""


class OllamaError(RepoWraithError):
    """Base error for Ollama API failures."""


class OllamaConnectionError(OllamaError):
    """Raised when Ollama cannot be reached."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an unexpected response."""
