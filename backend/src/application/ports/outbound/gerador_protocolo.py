"""Porta de saída: GeradorProtocolo (HEX-08) — formato SGOPI-AAAA-NNNNNN."""
from abc import ABC, abstractmethod


class GeradorProtocolo(ABC):
    @abstractmethod
    async def proximo(self, ano: int) -> str:
        """Devolve o próximo número de protocolo único para o ano informado."""
        ...


def formatar_protocolo(ano: int, sequencial: int) -> str:
    return f"SGOPI-{ano:04d}-{sequencial:06d}"
