"""
Porta de entrada: InterfaceRegistrarOcorrenciaPolicial

Contratos (ABCs e DTOs) que o adapter HTTP usa para acionar o caso de uso
sem conhecer sua implementação concreta.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class EnvolvidoInputDTO:
    nome: str
    tipo: str  # valor de TipoEnvolvido: VITIMA | TESTEMUNHA | SUSPEITO
    documento: str | None = None


@dataclass(frozen=True)
class TipificacaoInputDTO:
    artigo: str
    descricao: str


@dataclass(frozen=True)
class RegistrarOcorrenciaInput:
    agente_policial_id: UUID
    natureza: str
    descricao: str
    localizacao: str
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
    async def executar(
        self, input_dto: RegistrarOcorrenciaInput
    ) -> RegistrarOcorrenciaOutput:
        ...
