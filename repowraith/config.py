# ═════════════════ SURVEY ═════════════════

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".repowraith",
}

DEFAULT_IGNORE_DIR_SUFFIXES = {".egg-info"}
DEFAULT_IGNORE_EXTENSIONS = {".pyc", ".pyo", ".log", ".gitignore"}

# ═════════════════ CHUNKING ═══════════════

CHUNK_SIZE = 60
OVERLAP = 15

# ═════════════════ OLLAMA / MODELS ════════

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embed"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

LLM_MODEL = "qwen"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 1024
EMBED_MODEL = "embeddinggemma"
EMBED_BATCH_SIZE = 64

REQUEST_TIMEOUT_SECONDS = 45
GENERATE_TIMEOUT_SECONDS = 300

# ═════════════════ RETRIEVAL ══════════════

DEFAULT_TOP_K = 8

LEXICAL_WEIGHT = 0.5
FILENAME_WEIGHT = 1.0
TEST_FILE_WEIGHT = 0.5
BM25_K1 = 1.5
BM25_B = 0.75

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "does",
    "for",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "who",
    "why",
    "with",
    "work",
    "works",
    "code",
}
