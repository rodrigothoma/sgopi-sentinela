"""
Porta de entrada: InterfaceRegistrarOcorrenciaPolicial

Define o contrato que o adapter HTTP (controller FastAPI) usa para
acionar o caso de uso, sem conhecer a implementação concreta.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegistrarOcorrenciaInput:
    """DTO de entrada para o caso de uso de registro de ocorrência."""
    agente_policial_id: UUID
    descricao: str
    localizacao: str


@dataclass(frozen=True)
class RegistrarOcorrenciaOutput:
    """DTO de saída retornado ao adapter após o registro."""
    ocorrencia_id: UUID
    numero_protocolo: str
    status: str


class InterfaceRegistrarOcorrenciaPolicial(ABC):

    @abstractmethod
    async def executar(
        self, input_dto: RegistrarOcorrenciaInput
    ) -> RegistrarOcorrenciaOutput:
        ...
