"""Tests del cálculo del polígono edificable con retiros."""

from app.setbacks import compute_setback

# Lote cuadrado de ~20 m por lado cerca del ecuador (1° lat ≈ 111 km).
LOT = [
    (4.65, -74.05),
    (4.65018, -74.05),
    (4.65018, -74.049819),
    (4.65, -74.049819),
]


def test_retiro_contrae_el_lote():
    result = compute_setback(LOT, setback_m=3.0)

    assert result.valid
    assert len(result.buildable) >= 3
    # Lote ~20x20 m; con retiro de 3 m el edificable queda ~14x14 m.
    assert 190 <= result.lot_area_m2 <= 410
    assert 140 <= result.buildable_area_m2 <= 240
    assert result.buildable_area_m2 < result.lot_area_m2


def test_retiro_cero_mantiene_lote():
    result = compute_setback(LOT, setback_m=0.0)
    assert result.valid
    assert result.buildable_area_m2 == result.lot_area_m2


def test_retiro_excesivo_no_deja_area_edificable():
    result = compute_setback(LOT, setback_m=50.0)
    assert not result.valid
    assert result.buildable == []
    assert result.buildable_area_m2 == 0.0


def test_lote_invalido():
    assert not compute_setback(LOT[:2], setback_m=3.0).valid
    assert not compute_setback(LOT, setback_m=-1.0).valid
