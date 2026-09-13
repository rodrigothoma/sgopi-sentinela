"""Porta de saída: Relogio (HEX-07) — o domínio nunca chama datetime.now()."""
from abc import ABC, abstractmethod
from datetime import datetime


class Relogio(ABC):
    @abstractmethod
    def agora(self) -> datetime:
        """Instante atual com fuso horário (UTC)."""
        ...
