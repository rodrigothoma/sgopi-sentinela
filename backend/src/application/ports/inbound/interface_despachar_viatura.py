"""Portas de entrada: sugestão, despacho e encerramento de viaturas (RF02)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_gerir_viaturas import ViaturaOutput


@dataclass(frozen=True)
class ViaturaSugeridaOutput:
    viatura: ViaturaOutput
    distancia_km: float


@dataclass(frozen=True)
class SugestoesOutput:
    ocorrencia_id: UUID
    sugestoes: tuple[ViaturaSugeridaOutput, ...]
    sem_elegiveis: bool
    disponiveis_sem_posicao: tuple[ViaturaOutput, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DespacharInput:
    ocorrencia_id: UUID
    viatura_id: UUID
    observacoes: str | None = None


@dataclass(frozen=True)
class OrdemDespachoOutput:
    id: UUID
    numero: str
    ocorrencia_id: UUID
    viatura_id: UUID
    operador_id: UUID
    criada_em: str
    observacoes: str | None
    ativa: bool
    encerrada_em: str | None


@dataclass(frozen=True)
class EncerrarInput:
    ocorrencia_id: UUID
    desfecho: str


@dataclass(frozen=True)
class ListarOrdensInput:
    ocorrencia_id: UUID | None = None
    somente_ativas: bool = False
    limit: int = 100


class InterfaceSugerirViaturasProximas(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> SugestoesOutput: ...


class InterfaceDespacharViatura(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: DespacharInput) -> OrdemDespachoOutput: ...


class InterfaceEncerrarOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: EncerrarInput) -> OcorrenciaDetalheOutput: ...


class InterfaceListarOrdensDespacho(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: ListarOrdensInput) -> tuple[OrdemDespachoOutput, ...]: ...
