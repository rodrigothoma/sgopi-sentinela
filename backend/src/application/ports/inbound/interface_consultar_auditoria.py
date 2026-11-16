"""Porta de entrada: consulta de auditoria (RNF03 aceite 1) — somente Delegado/Supervisor."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from application.ports.inbound.ator import Ator

LIMITE_PADRAO_CONSULTA: int = 50  # tamanho da página da trilha
LIMITE_MAXIMO_CONSULTA: int = 500


@dataclass(frozen=True)
class ConsultarAuditoriaInput:
    entidade: str | None = None
    entidade_id: str | None = None
    operacao: str | None = None
    quem: UUID | None = None
    limit: int = LIMITE_PADRAO_CONSULTA
    offset: int = 0
    # Datas de calendário no fuso da operação, ambas inclusas.
    de: date | None = None
    ate: date | None = None


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


@dataclass(frozen=True)
class PaginaAuditoriaOutput:
    itens: tuple[RegistroAuditoriaOutput, ...]
    total: int
    limit: int
    offset: int


class InterfaceConsultarAuditoria(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: ConsultarAuditoriaInput) -> PaginaAuditoriaOutput:
        """Página da trilha, mais recentes primeiro, com o total para a paginação."""
