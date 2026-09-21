"""
Porta de entrada: arquivamento e exclusão lógica de ocorrência.

Ambos os atos exigem autorização do Delegado (papel verificado no caso de uso)
e um motivo obrigatório, gravado no histórico de status e na auditoria.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput


@dataclass(frozen=True)
class AutorizacaoDelegadoInput:
    ocorrencia_id: UUID
    motivo: str


class InterfaceArquivarOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AutorizacaoDelegadoInput) -> OcorrenciaDetalheOutput: ...


class InterfaceExcluirOcorrencia(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AutorizacaoDelegadoInput) -> OcorrenciaDetalheOutput: ...
