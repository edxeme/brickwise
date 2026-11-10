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

# Autenticación: firma de JWT y vigencia de la sesión en días
SECRET_KEY = os.getenv(
    "BRICKWISE_SECRET_KEY", "dev-secret-change-me-32-bytes-minimum!!"
)
TOKEN_TTL_DAYS = int(os.getenv("BRICKWISE_TOKEN_TTL_DAYS", "7"))

# Etiquetas legibles del semáforo de viabilidad
RATING_LABELS = {
    "viable": "Viable",
    "viable_con_condiciones": "Viable con condiciones",
    "no_viable": "No viable",
}
