"""Porta de saída: PortaAuditoria (RNF03) — registro append-only de operações sensíveis."""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.entity import RegistroAuditoria
from domain.auditoria.evento import EventoAuditoria


class PortaAuditoria(ABC):
    @abstractmethod
    async def registrar(self, evento: EventoAuditoria, contexto: ContextoAuditoria) -> None:
        """Grava o evento (o que aconteceu) com o contexto (quem, quando, de onde).

        Chamado dentro da unidade de trabalho da alteração: o registro entra na mesma
        transação e some junto se ela for desfeita.
        """

    @abstractmethod
    async def listar(
        self,
        entidade: str | None = None,
        entidade_id: str | None = None,
        operacao: str | None = None,
        quem: UUID | None = None,
        limit: int = 100,
    ) -> list[RegistroAuditoria]: ...
