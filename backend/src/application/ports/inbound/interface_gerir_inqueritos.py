"""Portas de entrada: Gestão de Inquéritos Policiais (RF06 / UC06)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass
class InstaurarInqueritoInput:
    ementa: str
    ocorrencias_iniciais_ids: list[UUID] | None = None


@dataclass
class VincularOcorrenciasInput:
    inquerito_id: UUID
    ocorrencias_ids: list[UUID]


@dataclass
class ConcluirInqueritoInput:
    inquerito_id: UUID
    relatorio_final: str


@dataclass
class OcorrenciaResumoInqueritoOutput:
    id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    data_hora_fato: str
    status: str


@dataclass
class InqueritoOutput:
    id: UUID
    numero: str
    ementa: str
    delegado_id: UUID
    status: str
    data_abertura: str
    atualizado_em: str
    ocorrencias: list[OcorrenciaResumoInqueritoOutput]
    relatorio_final: str | None = None
    motivo_arquivamento: str | None = None
    concluido_em: str | None = None


@dataclass
class ConexaoSugeridaOutput:
    ocorrencia_id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    motivo_conexao: str  # ex: "Mesmo suspeito: Fulano (CPF: ...)", "Proximidade: 450m"
    pontuacao_relevancia: int


class InterfaceInstaurarInquerito(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: InstaurarInqueritoInput) -> InqueritoOutput: ...


class InterfaceListarInqueritos(ABC):
    @abstractmethod
    async def executar(
        self, ator: Ator, status: list[str] | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[InqueritoOutput], int]: ...


class InterfaceObterInquerito(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, inquerito_id: UUID) -> InqueritoOutput: ...


class InterfaceVincularOcorrenciasInquerito(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: VincularOcorrenciasInput) -> InqueritoOutput: ...


class InterfaceBuscarConexoesOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, ocorrencia_pivo_id: UUID) -> list[ConexaoSugeridaOutput]: ...


class InterfaceConcluirInquerito(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: ConcluirInqueritoInput) -> InqueritoOutput: ...
