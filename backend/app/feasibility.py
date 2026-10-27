"""Motor de factibilidad: puntaje ponderado por criterios y semáforo de viabilidad.

Lógica pura, sin dependencias de base de datos, para que sea trivial de probar.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

MIN_WEIGHT, MAX_WEIGHT = 1, 5
MIN_SCORE, MAX_SCORE = 0.0, 100.0

# Un criterio con peso alto y calificación baja constituye riesgo crítico.
CRITICAL_WEIGHT_THRESHOLD = 4
CRITICAL_SCORE_THRESHOLD = 50.0


class Rating(str, Enum):
    VIABLE = "viable"
    CONDICIONES = "viable_con_condiciones"
    NO_VIABLE = "no_viable"


@dataclass(frozen=True)
class CriterionInput:
    category: str
    name: str
    weight: int
    score: float


@dataclass(frozen=True)
class CategoryScore:
    category: str
    score: float


@dataclass(frozen=True)
class FeasibilityResult:
    score: float
    rating: Rating
    by_category: list[CategoryScore] = field(default_factory=list)
    critical_flags: list[str] = field(default_factory=list)


def rating_for(score: float) -> Rating:
    if score >= 80:
        return Rating.VIABLE
    if score >= 60:
        return Rating.CONDICIONES
    return Rating.NO_VIABLE


def weighted_feasibility(criteria: Iterable[CriterionInput]) -> FeasibilityResult:
    """Puntaje global = Σ(score · peso) / Σpeso, con detalle por categoría.

    Bandas de semáforo: ≥ 80 viable, 60–79 viable con condiciones, < 60 no viable.
    """
    items = list(criteria)
    if not items:
        return FeasibilityResult(score=0.0, rating=Rating.NO_VIABLE)

    for criterion in items:
        if not MIN_WEIGHT <= criterion.weight <= MAX_WEIGHT:
            raise ValueError(
                f"weight fuera de rango ({MIN_WEIGHT}-{MAX_WEIGHT}): {criterion.weight}"
            )
        if not MIN_SCORE <= criterion.score <= MAX_SCORE:
            raise ValueError(
                f"score fuera de rango ({MIN_SCORE}-{MAX_SCORE}): {criterion.score}"
            )

    total_weight = sum(c.weight for c in items)
    score = sum(c.score * c.weight for c in items) / total_weight

    by_category: dict[str, tuple[float, int]] = {}
    for criterion in items:
        accumulated, weight = by_category.get(criterion.category, (0.0, 0))
        by_category[criterion.category] = (
            accumulated + criterion.score * criterion.weight,
            weight + criterion.weight,
        )
    categories = [
        CategoryScore(category=category, score=round(total / weight, 2))
        for category, (total, weight) in sorted(by_category.items())
    ]

    critical_flags = [
        c.name
        for c in items
        if c.weight >= CRITICAL_WEIGHT_THRESHOLD and c.score < CRITICAL_SCORE_THRESHOLD
    ]

    return FeasibilityResult(
        score=round(score, 2),
        rating=rating_for(score),
        by_category=categories,
        critical_flags=critical_flags,
    )
