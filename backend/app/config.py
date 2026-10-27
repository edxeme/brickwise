"""Configuración vía variables de entorno con valores por defecto para desarrollo."""

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://brickwise:brickwise@localhost:5433/brickwise",
)

# Embeddings locales vía Ollama (sin llamadas externas)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text")

# Proveedor de embeddings: "hash" (determinista, sin red) o "ollama" (semántico)
EMBEDDER = os.getenv("BRICKWISE_EMBEDDER", "hash")
