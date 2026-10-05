"""Portas de entrada: Gestão de Laudos Periciais (RF07 / UC07)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass
class SolicitarLaudoInput:
    tipo_pericia: str
    descricao_solicitacao: str
    ocorrencia_id: UUID | None = None
    inquerito_id: UUID | None = None
    item_apreendido_id: UUID | None = None


@dataclass
class AnexarLaudoInput:
    laudo_id: UUID
    conclusoes_tecnicas: str
    conteudo_arquivo: bytes
    nome_arquivo: str


@dataclass
class LaudoOutput:
    id: UUID
    numero_referencia: str
    tipo_pericia: str
    descricao_solicitacao: str
    solicitante_id: UUID
    status: str
    solicitado_em: str
    atualizado_em: str
    perito_id: UUID | None = None
    ocorrencia_id: UUID | None = None
    inquerito_id: UUID | None = None
    item_apreendido_id: UUID | None = None
    conclusoes_tecnicas: str | None = None
    arquivo_nome: str | None = None
    hash_sha256: str | None = None
    concluido_em: str | None = None


class InterfaceSolicitarLaudo(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: SolicitarLaudoInput) -> LaudoOutput: ...


class InterfaceAnexarLaudo(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados: AnexarLaudoInput) -> LaudoOutput: ...


class InterfaceListarLaudos(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        status: list[str] | None = None,
        ocorrencia_id: UUID | None = None,
        inquerito_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LaudoOutput], int]: ...


class InterfaceObterLaudo(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, laudo_id: UUID) -> LaudoOutput: ...


@dataclass(frozen=True)
class ArquivoLaudoOutput:
    """PDF homologado, já conferido contra o SHA-256 registrado na anexação."""

    conteudo: bytes
    nome_arquivo: str
    hash_sha256: str


class InterfaceBaixarArquivoLaudo(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, laudo_id: UUID) -> ArquivoLaudoOutput: ...
