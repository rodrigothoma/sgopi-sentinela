"""Porta de entrada: redefinição da prioridade da ocorrência pelo Delegado (sugestão #7 — RF04)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput


@dataclass(frozen=True)
class RedefinirPrioridadeInput:
    ocorrencia_id: UUID
    prioridade: str  # BAIXA | MEDIA | ALTA | URGENTE
    justificativa: str


class InterfaceRedefinirPrioridade(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: RedefinirPrioridadeInput) -> OcorrenciaDetalheOutput: ...
