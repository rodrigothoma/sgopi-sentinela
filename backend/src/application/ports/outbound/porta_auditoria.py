"""Porta de saída: PortaAuditoria (RNF03) — registro append-only de operações sensíveis."""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.entity import RegistroAuditoria
from domain.auditoria.evento import EventoAuditoria


class PortaAuditoria(ABC):
    @abstractmethod
    async def registrar(self, evento: EventoAuditoria | RegistroAuditoria, contexto: ContextoAuditoria | None = None) -> None:
        """Grava o evento com o contexto (quem/quando/onde) na mesma transação da alteração.

        ``RegistroAuditoria`` pronto ainda é aceito durante a migração para eventos tipados.
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


def como_registro(evento: EventoAuditoria | RegistroAuditoria, contexto: ContextoAuditoria | None) -> RegistroAuditoria:
    """Converte o evento em registro persistível (Template Method do evento)."""
    if isinstance(evento, RegistroAuditoria):
        return evento
    if contexto is None:
        raise ValueError(f"{type(evento).__name__}: contexto de auditoria obrigatório.")
    return evento.para_registro(contexto)
