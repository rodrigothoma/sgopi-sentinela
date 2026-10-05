"""Porta de saída: GeradorNumeroLaudo — formato LP-AAAA-NNNNNN (RF07)."""
from abc import ABC, abstractmethod


class GeradorNumeroLaudo(ABC):
    @abstractmethod
    async def proximo(self, ano: int) -> str: ...


def formatar_numero_laudo(ano: int, sequencial: int) -> str:
    return f"LP-{ano:04d}-{sequencial:06d}"
