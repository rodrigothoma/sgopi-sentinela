"""
Value object Coordenada e cálculo de distância (DEC-03, DEC-05).

Haversine sobre a esfera terrestre (raio médio 6371,0088 km). Puro Python.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from domain.shared.exceptions import ValorInvalidoError

RAIO_TERRA_KM = 6371.0088


@dataclass(frozen=True)
class Coordenada:
    """Par latitude/longitude em graus decimais (WGS-84)."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not isinstance(self.latitude, (int, float)) or not isinstance(self.longitude, (int, float)):
            raise ValorInvalidoError("Coordenada deve ser numérica.", chave="geo.coordenada_invalida")
        if math.isnan(self.latitude) or math.isnan(self.longitude):
            raise ValorInvalidoError("Coordenada deve ser numérica.", chave="geo.coordenada_invalida")
        if not -90.0 <= self.latitude <= 90.0:
            raise ValorInvalidoError(
                f"Latitude fora da faixa [-90, 90]: {self.latitude}", chave="geo.latitude_fora_da_faixa"
            )
        if not -180.0 <= self.longitude <= 180.0:
            raise ValorInvalidoError(
                f"Longitude fora da faixa [-180, 180]: {self.longitude}", chave="geo.longitude_fora_da_faixa"
            )

    def distancia_km(self, outra: Coordenada) -> float:
        return calcular_distancia_km(self, outra)


def calcular_distancia_km(a: Coordenada, b: Coordenada) -> float:
    """Distância geodésica (Haversine) entre duas coordenadas, em quilômetros."""
    lat1, lon1 = math.radians(a.latitude), math.radians(a.longitude)
    lat2, lon2 = math.radians(b.latitude), math.radians(b.longitude)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(h))
