"""Porta de saída: PublicadorEventos (DEC-06 / RF17)."""
from abc import ABC, abstractmethod

from domain.shared.eventos import EventoDominio


class PublicadorEventos(ABC):
    @abstractmethod
    async def publicar(self, evento: EventoDominio) -> None: ...
