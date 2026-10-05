"""Porta de saída: PublicadorEventos (DEC-06 / RF02 / RNF01)."""
from abc import ABC, abstractmethod

from domain.shared.eventos import EventoDominio


class PublicadorEventos(ABC):
    @abstractmethod
    async def publicar(self, evento: EventoDominio) -> None: ...
