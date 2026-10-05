"""Porta de entrada para anexar evidências digitais a uma ocorrência (RF01)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class AnexarEvidenciaInput:
    ocorrencia_id: UUID
    nome_arquivo: str
    tipo_mime: str
    conteudo: bytes


@dataclass(frozen=True)
class EvidenciaOutput:
    id: UUID
    nome_original: str
    formato: str
    tamanho: int
    hash_sha256: str
    enviada_em: str


class InterfaceAnexarEvidencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AnexarEvidenciaInput) -> EvidenciaOutput: ...
