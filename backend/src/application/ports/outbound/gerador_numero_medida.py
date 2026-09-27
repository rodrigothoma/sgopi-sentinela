"""Porta de saída: GeradorNumeroMedida — formato MP-AAAA-NNNNNN (RF09)."""
from abc import ABC, abstractmethod


class GeradorNumeroMedida(ABC):
    @abstractmethod
    async def proximo(self, ano: int) -> str: ...


def formatar_numero_medida(ano: int, sequencial: int) -> str:
    return f"MP-{ano:04d}-{sequencial:06d}"
