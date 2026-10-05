"""Porta de saída: CredencialDispositivo (RF02 / N12) — identidade do rastreador GPS de cada viatura."""
from abc import ABC, abstractmethod
from uuid import UUID


class CredencialDispositivo(ABC):
    @abstractmethod
    def emitir(self, viatura_id: UUID) -> str:
        """Credencial do rastreador desta viatura (só vale para ela)."""

    @abstractmethod
    def confere(self, viatura_id: UUID, credencial: str) -> bool:
        """True se a credencial pertence ao rastreador da viatura informada."""
