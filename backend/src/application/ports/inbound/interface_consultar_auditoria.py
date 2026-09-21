"""Porta de entrada: consulta de auditoria (RF20 aceite 1) — somente Delegado/Supervisor."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from application.ports.inbound.ator import Ator


LIMITE_PADRAO_CONSULTA: int = 100
LIMITE_MAXIMO_CONSULTA: int = 500


@dataclass(frozen=True)
class ConsultarAuditoriaInput:
    entidade: str | None = None
    entidade_id: str | None = None
    operacao: str | None = None
    quem: UUID | None = None
    limit: int = LIMITE_PADRAO_CONSULTA


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
    autor_nome: str | None = None
    autor_papel: str | None = None
    identificador_amigavel: str | None = None


class InterfaceConsultarAuditoria(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> tuple[RegistroAuditoriaOutput, ...]: ...
