"""Escala única de prioridade (gravidade/urgência) usada por ocorrências e ofícios interagências."""
from __future__ import annotations

from enum import Enum


class Prioridade(str, Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"

    @property
    def peso(self) -> int:
        """Ordem de atendimento: quanto maior, mais cedo (URGENTE=4 … BAIXA=1)."""
        return _PESOS[self]


_PESOS = {Prioridade.BAIXA: 1, Prioridade.MEDIA: 2, Prioridade.ALTA: 3, Prioridade.URGENTE: 4}
