import pytest

from app.feasibility import CriterionInput, Rating, weighted_feasibility


def crit(name="acceso vehicular", category="tecnica", weight=3, score=80):
    return CriterionInput(category=category, name=name, weight=weight, score=score)


def test_promedio_ponderado_basico():
    result = weighted_feasibility([crit(weight=1, score=100), crit(weight=3, score=0)])
    assert result.score == 25.0
    assert result.rating is Rating.NO_VIABLE


def test_sin_criterios():
    result = weighted_feasibility([])
    assert result.score == 0.0
    assert result.rating is Rating.NO_VIABLE
    assert result.by_category == []
    assert result.critical_flags == []


def test_bandas_semaforo():
    assert weighted_feasibility([crit(score=85)]).rating is Rating.VIABLE
    assert weighted_feasibility([crit(score=70)]).rating is Rating.CONDICIONES
    assert weighted_feasibility([crit(score=59)]).rating is Rating.NO_VIABLE


def test_agrupacion_por_categoria():
    result = weighted_feasibility(
        [
            crit(name="uso de suelo", category="normativa", weight=2, score=90),
            crit(name="estructura", category="tecnica", weight=2, score=70),
            crit(name="acabados", category="tecnica", weight=2, score=90),
        ]
    )
    scores = {c.category: c.score for c in result.by_category}
    assert scores == {"normativa": 90.0, "tecnica": 80.0}


def test_riesgo_critico():
    result = weighted_feasibility([crit(name="servicios públicos", weight=5, score=30)])
    assert result.critical_flags == ["servicios públicos"]


def test_sin_riesgo_critico_con_score_alto():
    result = weighted_feasibility([crit(weight=5, score=60)])
    assert result.critical_flags == []


def test_pesos_y_scores_fuera_de_rango():
    with pytest.raises(ValueError):
        weighted_feasibility([crit(weight=6)])
    with pytest.raises(ValueError):
        weighted_feasibility([crit(weight=0)])
    with pytest.raises(ValueError):
        weighted_feasibility([crit(score=120)])
