"""Porta de saída: GeradorNumeroOrdem — formato OD-AAAA-NNNNNN (RF18)."""
from abc import ABC, abstractmethod


class GeradorNumeroOrdem(ABC):
    @abstractmethod
    async def proximo(self, ano: int) -> str: ...


def formatar_numero_ordem(ano: int, sequencial: int) -> str:
    return f"OD-{ano:04d}-{sequencial:06d}"
