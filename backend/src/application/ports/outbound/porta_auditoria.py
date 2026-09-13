"""Porta de saída: PortaAuditoria (RF20) — registro append-only de operações sensíveis."""
from abc import ABC, abstractmethod

from domain.auditoria.entity import RegistroAuditoria


class PortaAuditoria(ABC):
    @abstractmethod
    async def registrar(self, registro: RegistroAuditoria) -> None: ...

    @abstractmethod
    async def listar(
        self, entidade: str | None = None, entidade_id: str | None = None, limit: int = 100
    ) -> list[RegistroAuditoria]: ...
