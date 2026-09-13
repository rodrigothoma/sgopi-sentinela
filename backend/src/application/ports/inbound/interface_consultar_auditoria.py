"""Porta de entrada: consulta de auditoria (RF20 aceite 1) — somente Delegado/Supervisor."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class ConsultarAuditoriaInput:
    entidade: str | None = None
    entidade_id: str | None = None
    limit: int = 100


@dataclass(frozen=True)
class RegistroAuditoriaOutput:
    id: UUID
    quem: UUID | None
    quando: str
    operacao: str
    entidade: str
    entidade_id: str | None
    dados_antes: dict[str, Any] | None
    dados_depois: dict[str, Any] | None
    ip: str | None


class InterfaceConsultarAuditoria(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> tuple[RegistroAuditoriaOutput, ...]: ...
