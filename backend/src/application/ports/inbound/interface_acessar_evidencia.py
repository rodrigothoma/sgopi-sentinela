"""Portas de entrada para conferir e baixar evidências digitais (RF01)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from domain.ocorrencia.entity import EstadoIntegridadeEvidencia

__all__ = ["EstadoIntegridadeEvidencia"]


@dataclass(frozen=True)
class IntegridadeEvidenciaOutput:
    evidencia_id: UUID
    estado: EstadoIntegridadeEvidencia
    hash_armazenado: str
    hash_recalculado: str
    verificado_em: datetime  # serializado na borda HTTP


@dataclass(frozen=True)
class DownloadEvidenciaOutput:
    evidencia_id: UUID
    nome_original: str
    formato: str
    tamanho: int
    hash_sha256: str
    conteudo: bytes


class InterfaceVerificarIntegridadeEvidencia(ABC):
    @abstractmethod
    async def executar(
        self, ator: Ator, ocorrencia_id: UUID, evidencia_id: UUID
    ) -> IntegridadeEvidenciaOutput: ...


class InterfaceObterEvidenciaParaDownload(ABC):
    @abstractmethod
    async def executar(
        self, ator: Ator, ocorrencia_id: UUID, evidencia_id: UUID
    ) -> DownloadEvidenciaOutput: ...
