"""Portas de entrada: gestão de frota e telemetria (RF02)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class CadastrarViaturaInput:
    prefixo: str
    placa: str


@dataclass(frozen=True)
class AlterarSituacaoInput:
    viatura_id: UUID
    situacao: str  # DISPONIVEL | INDISPONIVEL (manual)


@dataclass(frozen=True)
class ViaturaOutput:
    id: UUID
    prefixo: str
    placa: str
    situacao: str
    latitude: float | None
    longitude: float | None
    posicao_registrada_em: str | None
    sinal: str  # OK | SEM_SINAL | SEM_POSICAO
    versao: int


@dataclass(frozen=True)
class RegistrarPosicaoInput:
    viatura_id: UUID
    latitude: float
    longitude: float
    registrada_em: datetime
    origem: str = "http"


class InterfaceCadastrarViatura(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: CadastrarViaturaInput) -> ViaturaOutput: ...


class InterfaceAlterarSituacaoViatura(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AlterarSituacaoInput) -> ViaturaOutput: ...


class InterfaceListarViaturas(ABC):
    @abstractmethod
    async def executar(self, ator: Ator) -> tuple[ViaturaOutput, ...]: ...


class InterfaceRegistrarPosicaoViatura(ABC):
    @abstractmethod
    async def executar(self, input_dto: RegistrarPosicaoInput) -> ViaturaOutput: ...
