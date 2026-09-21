"""Porta de saída: PortaAuditoria (RNF03) — registro append-only de operações sensíveis."""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.auditoria.entity import RegistroAuditoria


class PortaAuditoria(ABC):
    @abstractmethod
    async def registrar(self, registro: RegistroAuditoria) -> None: ...

    @abstractmethod
    async def listar(
        self,
        entidade: str | None = None,
        entidade_id: str | None = None,
        operacao: str | None = None,
        quem: UUID | None = None,
        limit: int = 100,
    ) -> list[RegistroAuditoria]: ...
