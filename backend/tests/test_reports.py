"""Tests del informe de factibilidad en Markdown."""

from app import models, reports


def _project() -> models.Project:
    project = models.Project(
        name="Torre Norte",
        location="Bogotá",
        typology=models.Typology.MIXTO,
        area_m2=2500,
        budget_cop=8_500_000_000,
        criteria=[
            models.Criterion(
                category=models.Category.TECNICA,
                name="Disponibilidad de redes",
                weight=4,
                score=85,
            ),
            models.Criterion(
                category=models.Category.NORMATIVA,
                name="Cumplimiento de retiros",
                weight=5,
                score=40,
            ),
        ],
    )
    return project


def test_informe_contiene_secciones_clave():
    report = reports.build_report(_project())

    assert report.startswith("# Informe de factibilidad — Torre Norte")
    assert "Semáforo de viabilidad" in report
    assert "Riesgos críticos" in report
    assert "Cumplimiento de retiros" in report  # riesgo crítico (peso 5, score 40)
    assert "Viable con condiciones" in report  # score = (85*4 + 40*5)/9 ≈ 60


def test_informe_sin_criterios():
    project = models.Project(
        name="Lote vacío",
        location="Medellín",
        typology=models.Typology.VIVIENDA,
        area_m2=500,
        budget_cop=1_000_000_000,
    )
    report = reports.build_report(project)
    assert "No viable" in report
    assert "_Sin criterios._" in report
