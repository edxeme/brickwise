"""Exportación de informes de factibilidad en Markdown."""

import datetime as dt

from . import feasibility, models
from .config import RATING_LABELS

TYPLOGY_LABELS = {
    models.Typology.VIVIENDA: "Vivienda",
    models.Typology.COMERCIO: "Comercio",
    models.Typology.INDUSTRIA: "Industria",
    models.Typology.MIXTO: "Mixto",
    models.Typology.INSTITUCIONAL: "Institucional",
}

CATEGORY_LABELS = {
    "tecnica": "Técnica",
    "normativa": "Normativa",
    "economica": "Económica",
    "mercado": "Mercado",
}


def _cop(value: float) -> str:
    return f"COL $ {value:,.0f}"


def _rating_line(result: feasibility.FeasibilityResult) -> str:
    label = RATING_LABELS[result.rating.value]
    return f"**{label}** (score {result.score:.1f} / 100)"


def build_report(project: models.Project) -> str:
    """Informe Markdown del proyecto: semáforo, desglose, criterios y alternativas."""
    result = feasibility.weighted_feasibility(
        feasibility.CriterionInput(
            category=c.category.value,
            name=c.name,
            weight=c.weight,
            score=float(c.score),
        )
        for c in project.criteria
    )

    lines: list[str] = []
    lines.append(f"# Informe de factibilidad — {project.name}")
    lines.append(f"_Generado el {dt.date.today().isoformat()}_")
    lines.append("")
    lines.append("## Datos del proyecto")
    lines.append(f"- **Ubicación:** {project.location}")
    typology = TYPLOGY_LABELS.get(models.Typology(project.typology), str(project.typology))
    lines.append(f"- **Tipología:** {typology}")
    lines.append(f"- **Área:** {float(project.area_m2):,.0f} m²")
    lines.append(f"- **Presupuesto:** {_cop(float(project.budget_cop))}")
    lines.append("")
    lines.append("## Semáforo de viabilidad")
    lines.append(_rating_line(result))
    lines.append("")

    lines.append("### Desglose por categoría")
    if result.by_category:
        lines.append("| Categoría | Score |")
        lines.append("| :--- | ---: |")
        for category in result.by_category:
            label = CATEGORY_LABELS.get(category.category, category.category)
            lines.append(f"| {label} | {category.score:.1f} |")
    else:
        lines.append("_Sin criterios evaluados._")
    lines.append("")

    lines.append("### Riesgos críticos")
    if result.critical_flags:
        for name in result.critical_flags:
            lines.append(f"- ⚠️ {name} (peso alto con calificación baja)")
    else:
        lines.append("_Ninguno identificado._")
    lines.append("")

    lines.append("### Criterios")
    if project.criteria:
        lines.append("| Criterio | Categoría | Peso | Calificación | Notas |")
        lines.append("| :--- | :--- | ---: | ---: | :--- |")
        for c in project.criteria:
            category = CATEGORY_LABELS.get(c.category.value, c.category.value)
            notes = c.notes or ""
            lines.append(
                f"| {c.name} | {category} | {c.weight} | {float(c.score):.0f} | {notes} |"
            )
    else:
        lines.append("_Sin criterios._")
    lines.append("")

    if project.alternatives:
        lines.append("## Comparación de alternativas de emplazamiento")
        lines.append("| Alternativa | Score | Rating | Criterios |")
        lines.append("| :--- | ---: | :--- | ---: |")
        ranked = sorted(
            project.alternatives,
            key=lambda a: feasibility.weighted_feasibility(
                feasibility.CriterionInput(
                    category=c.category.value,
                    name=c.name,
                    weight=c.weight,
                    score=float(c.score),
                )
                for c in a.criteria
            ).score,
            reverse=True,
        )
        for alternative in ranked:
            alt_result = feasibility.weighted_feasibility(
                feasibility.CriterionInput(
                    category=c.category.value,
                    name=c.name,
                    weight=c.weight,
                    score=float(c.score),
                )
                for c in alternative.criteria
            )
            label = RATING_LABELS[alt_result.rating.value]
            lines.append(
                f"| {alternative.name} | {alt_result.score:.1f} | {label} | {len(alternative.criteria)} |"
            )
        lines.append("")

    return "\n".join(lines)
