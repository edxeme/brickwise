"""Ingesta y búsqueda semántica de documentos normativos sobre pgvector."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .embeddings import EmbeddingProvider, top_k_by_cosine
from .models import RegulationChunk


def chunk_text(text: str, max_chars: int = 900) -> list[str]:
    """Divide un documento en fragmentos que respetan párrafos.

    Un párrafo mayor que `max_chars` se conserva completo (sin cortes a mitad
    de norma) para no perder contexto normativo.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def ingest_document(
    session: Session,
    embedder: EmbeddingProvider,
    *,
    document_title: str,
    content: str,
    project_id: int | None = None,
    section: str | None = None,
) -> list[RegulationChunk]:
    """Divide el documento, calcula embeddings y persiste los fragmentos."""
    chunks = chunk_text(content)
    if not chunks:
        return []
    vectors = embedder.embed(chunks)
    rows = [
        RegulationChunk(
            project_id=project_id,
            document_title=document_title,
            section=section,
            content=chunk,
            embedding=vector,
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    session.add_all(rows)
    session.commit()
    return rows


def search_regulations(
    session: Session,
    embedder: EmbeddingProvider,
    query: str,
    *,
    project_id: int | None = None,
    top_k: int = 5,
) -> list[tuple[RegulationChunk, float]]:
    """Búsqueda semántica por similitud de coseno contra los fragmentos ingestados."""
    query_vector = embedder.embed([query])[0]

    stmt = select(RegulationChunk)
    if project_id is not None:
        stmt = stmt.where(RegulationChunk.project_id == project_id)
    rows = list(session.scalars(stmt))
    if not rows:
        return []

    ranking = top_k_by_cosine(
        query_vector,
        [(row.id, list(row.embedding)) for row in rows],
        k=top_k,
    )
    by_id = {row.id: row for row in rows}
    return [(by_id[item_id], similarity) for item_id, similarity in ranking]
