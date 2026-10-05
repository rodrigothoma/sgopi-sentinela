"""Porta de saída: GeradorNumeroInquerito — formato IP-AAAA-NNNNNN (RF06)."""
from abc import ABC, abstractmethod


class GeradorNumeroInquerito(ABC):
    @abstractmethod
    async def proximo(self, ano: int) -> str: ...


def formatar_numero_inquerito(ano: int, sequencial: int) -> str:
    return f"IP-{ano:04d}-{sequencial:06d}"
