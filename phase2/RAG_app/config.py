from __future__ import annotations

COLLECTION_NAME = "Document"

# Text splitting parameters
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Hybrid search parameters
DEFAULT_HYBRID_ALPHA = 0.5  # 0 → pure BM25, 1 → pure vector

# Ollama LLM settings (used by qa_loop.py)
OLLAMA_MODEL = "gemma4:e4b-it-qat"
OLLAMA_URL = "http://localhost:11434"
