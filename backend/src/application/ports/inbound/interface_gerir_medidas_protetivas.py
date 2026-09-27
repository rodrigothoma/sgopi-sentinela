"""Portas de entrada: Gestão de Medidas Protetivas (RF09 / UC09)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass
class ConcederMedidaInput:
    ocorrencia_id: UUID
    vitima_id: UUID
    agressor_id: UUID
    tipos_restricao: list[str]
    prazo_dias: int
    data_inicio: date | None = None
    distancia_minima_metros: int | None = None
    condicoes_especificas: str | None = None


@dataclass
class RenovarMedidaInput:
    medida_id: UUID
    dias_adicionais: int
    justificativa: str


@dataclass
class RevogarMedidaInput:
    medida_id: UUID
    motivo: str


@dataclass
class MedidaProtetivaOutput:
    id: UUID
    numero_referencia: str
    ocorrencia_id: UUID
    delegado_id: UUID
    vitima_id: UUID
    agressor_id: UUID
    tipos_restricao: list[str]
    distancia_minima_metros: int | None
    data_inicio: str
    prazo_dias: int
    data_vencimento: str
    dias_restantes: int
    status: str
    condicoes_especificas: str | None
    motivo_revogacao: str | None
    justificativa_renovacao: str | None
    criada_em: str


class InterfaceConcederMedida(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: ConcederMedidaInput) -> MedidaProtetivaOutput: ...


class InterfaceRenovarMedida(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: RenovarMedidaInput) -> MedidaProtetivaOutput: ...


class InterfaceRevogarMedida(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: RevogarMedidaInput) -> MedidaProtetivaOutput: ...


class InterfaceListarMedidas(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        status: list[str] | None = None,
        ocorrencia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MedidaProtetivaOutput], int]: ...
