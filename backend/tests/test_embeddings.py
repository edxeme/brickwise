import pytest

from app.embeddings import HashEmbedder, cosine_similarity, top_k_by_cosine


def test_hash_embedder_determinista_y_normalizado():
    embedder = HashEmbedder(dim=16)
    v1 = embedder.embed(["uso de suelo residencial"])[0]
    v2 = embedder.embed(["uso de suelo residencial"])[0]
    assert v1 == v2
    assert len(v1) == 16
    assert abs(sum(x * x for x in v1) - 1.0) < 1e-9


def test_hash_embedder_distingue_textos():
    embedder = HashEmbedder(dim=16)
    v1 = embedder.embed(["retiro urbano"])[0]
    v2 = embedder.embed(["geotecnia"])[0]
    assert v1 != v2


def test_coseno_valores_conocidos():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0, 0.0], []) == 0.0


def test_top_k_orden_descendente():
    query = [1.0, 0.0]
    items = [(1, [1.0, 0.0]), (2, [0.0, 1.0]), (3, [0.7071, 0.7071])]
    top = top_k_by_cosine(query, items, k=2)
    assert [item_id for item_id, _ in top] == [1, 3]


def test_top_k_respeta_k():
    items = [(i, [float(i), 1.0]) for i in range(1, 6)]
    top = top_k_by_cosine([1.0, 0.0], items, k=3)
    assert len(top) == 3
