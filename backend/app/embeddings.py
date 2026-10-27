"""Proveedores de embeddings: Ollama local y uno determinista para pruebas.

El proveedor por defecto es el determinista (sin red); con Ollama corriendo se
activa `BRICKWISE_EMBEDDER=ollama` para búsqueda semántica real.
"""

import hashlib
import math
from typing import Protocol

import httpx

from .config import EMBEDDER, OLLAMA_BASE_URL, OLLAMA_MODEL


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OllamaEmbedder:
    """Embeddings con un modelo servido por Ollama (p. ej. nomic-embed-text)."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = httpx.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": texts},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]


class HashEmbedder:
    """Embedding determinista basado en hash de tokens.

    No captura semántica real; permite probar el pipeline completo y desarrollar
    sin depender de un modelo local. Mantener la dimensión fija por corrida para
    que los vectores almacenados sigan siendo comparables.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in text.lower().split():
            digest = hashlib.md5(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            vector[index] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def make_embedder() -> EmbeddingProvider:
    if EMBEDDER == "ollama":
        return OllamaEmbedder()
    return HashEmbedder()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


def top_k_by_cosine(
    query: list[float], items: list[tuple[int, list[float]]], k: int = 5
) -> list[tuple[int, float]]:
    """Devuelve los k ítems más similares como (id, similitud), en orden descendente."""
    scored = [(item_id, cosine_similarity(query, vector)) for item_id, vector in items]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:k]
