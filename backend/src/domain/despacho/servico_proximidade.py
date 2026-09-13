"""
Serviço de domínio puro: sugestão das N viaturas mais próximas (RF18, DEC-05).

Elegíveis: DISPONIVEL **e** com posição válida (idade ≤ limite — RNF04*).
Ordenação por distância Haversine crescente; empate por prefixo.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.shared.geo import Coordenada, calcular_distancia_km
from domain.viatura.entity import Viatura


@dataclass(frozen=True)
class ViaturaSugerida:
    viatura: Viatura
    distancia_km: float


def sugerir_viaturas_proximas(
    alvo: Coordenada, viaturas: list[Viatura], agora: datetime, max_idade_segundos: int, quantidade: int = 3
) -> list[ViaturaSugerida]:
    elegiveis = [v for v in viaturas if v.despachavel and v.posicao_valida(agora, max_idade_segundos)]
    sugeridas = [
        ViaturaSugerida(viatura=v, distancia_km=round(calcular_distancia_km(alvo, v.ultima_posicao.coordenada), 3))  # type: ignore[union-attr]
        for v in elegiveis
    ]
    sugeridas.sort(key=lambda s: (s.distancia_km, s.viatura.prefixo))
    return sugeridas[: max(0, quantidade)]
