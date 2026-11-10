"""Retiros normativos: polígono edificable a partir del lote.

El lote llega como coordenadas geográficas (lat, lon); se trabaja en metros con
una proyección local equirectangular (precisión suficiente para lotes urbanos)
y se contrae el polígono con un buffer negativo del retiro en metros.
"""

import math
from dataclasses import dataclass

from shapely.geometry import Polygon

METERS_PER_DEGREE_LAT = 111_320.0

MIN_BUILDABLE_AREA_M2 = 1.0


@dataclass(frozen=True)
class SetbackResult:
    valid: bool
    message: str
    buildable: list[tuple[float, float]]  # (lat, lon) del polígono edificable
    lot_area_m2: float
    buildable_area_m2: float


def _local_projection(coords: list[tuple[float, float]]):
    """Convierte (lat, lon) a metros respecto al centroide del lote."""
    center_lat = sum(lat for lat, _ in coords) / len(coords)
    meters_per_deg_lon = METERS_PER_DEGREE_LAT * math.cos(math.radians(center_lat))
    origin_lon = sum(lon for _, lon in coords) / len(coords)
    projected = [
        ((lon - origin_lon) * meters_per_deg_lon, (lat - center_lat) * METERS_PER_DEGREE_LAT)
        for lat, lon in coords
    ]
    return projected, center_lat, origin_lon, meters_per_deg_lon


def _to_coords(projected, center_lat: float, origin_lon: float, m_per_deg_lon: float):
    return [
        (center_lat + y / METERS_PER_DEGREE_LAT, origin_lon + x / m_per_deg_lon)
        for x, y in projected
    ]


def compute_setback(
    coordinates: list[tuple[float, float]], setback_m: float
) -> SetbackResult:
    """Polígono edificable = lote contraído `setback_m` por todos los bordes."""
    if len(coordinates) < 3:
        return SetbackResult(False, "El lote requiere al menos 3 vértices.", [], 0.0, 0.0)
    if setback_m < 0:
        return SetbackResult(False, "El retiro no puede ser negativo.", [], 0.0, 0.0)

    projected, center_lat, origin_lon, m_per_deg_lon = _local_projection(coordinates)
    lot = Polygon(projected)
    if not lot.is_valid:
        return SetbackResult(
            False, "El polígono del lote es inválido (vértices cruzados).", [], 0.0, 0.0
        )

    buildable = lot.buffer(-setback_m)
    lot_area = abs(lot.area)
    buildable_area = (
        abs(buildable.area) if not buildable.is_empty and setback_m > 0 else lot_area
    )
    if buildable.is_empty or buildable_area < MIN_BUILDABLE_AREA_M2:
        return SetbackResult(
            False,
            f"Con un retiro de {setback_m:.0f} m no queda área edificable.",
            [],
            round(lot_area, 2),
            0.0,
        )

    coords = _to_coords(list(buildable.exterior.coords), center_lat, origin_lon, m_per_deg_lon)
    return SetbackResult(
        valid=True,
        message="Polígono edificable calculado.",
        buildable=coords,
        lot_area_m2=round(lot_area, 2),
        buildable_area_m2=round(buildable_area, 2),
    )
