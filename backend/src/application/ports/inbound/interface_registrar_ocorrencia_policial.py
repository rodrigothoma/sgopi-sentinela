"""
Porta de entrada: InterfaceRegistrarOcorrenciaPolicial (RF01*)

Contratos (ABCs e DTOs) que o adapter HTTP usa para acionar o caso de uso
sem conhecer sua implementação concreta. O ator vem do token (nunca do body).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class EnvolvidoInputDTO:
    nome: str
    tipo: str  # valor de TipoEnvolvido: VITIMA | TESTEMUNHA | SUSPEITO | COMUNICANTE
    documento: str | None = None
    email: str | None = None
    telefone: str | None = None


@dataclass(frozen=True)
class TipificacaoInputDTO:
    artigo: str
    descricao: str


@dataclass(frozen=True)
class RegistrarOcorrenciaInput:
    natureza: str
    descricao: str
    localizacao: str
    latitude: float
    longitude: float
    data_hora_fato: datetime
    tipificacoes: tuple[TipificacaoInputDTO, ...] = field(default_factory=tuple)
    envolvidos: tuple[EnvolvidoInputDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RegistrarOcorrenciaOutput:
    ocorrencia_id: UUID
    numero_protocolo: str
    status: str
    criada_em: str  # ISO 8601


class InterfaceRegistrarOcorrenciaPolicial(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: RegistrarOcorrenciaInput) -> RegistrarOcorrenciaOutput: ...
