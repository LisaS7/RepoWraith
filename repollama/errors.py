class RepoLlamaError(RuntimeError):
    """Base error for RepoLlama failures."""


class OllamaError(RepoLlamaError):
    """Base error for Ollama API failures."""


class OllamaConnectionError(OllamaError):
    """Raised when Ollama cannot be reached."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an unexpected response."""
