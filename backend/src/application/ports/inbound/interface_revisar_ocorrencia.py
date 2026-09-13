"""Porta de entrada: revisão pelo Delegado (RF04*) e correção/reenvio pelo Agente (RF14)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_registrar_ocorrencia_policial import EnvolvidoInputDTO, TipificacaoInputDTO


@dataclass(frozen=True)
class DecisaoRevisaoInput:
    ocorrencia_id: UUID
    justificativa: str | None = None


@dataclass(frozen=True)
class CorrigirOcorrenciaInput:
    ocorrencia_id: UUID
    natureza: str | None = None
    descricao: str | None = None
    localizacao: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    data_hora_fato: datetime | None = None
    envolvidos: tuple[EnvolvidoInputDTO, ...] | None = None
    tipificacoes: tuple[TipificacaoInputDTO, ...] | None = field(default=None)


class InterfaceValidarOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput: ...


class InterfaceDevolverParaCorrecao(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput: ...


class InterfaceRejeitarOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput: ...


class InterfaceCorrigirOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: CorrigirOcorrenciaInput) -> OcorrenciaDetalheOutput: ...


class InterfaceReenviarOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> OcorrenciaDetalheOutput: ...
