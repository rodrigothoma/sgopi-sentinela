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
    tipo: str  # valor de TipoEnvolvido: VITIMA | TESTEMUNHA | SUSPEITO
    documento: str | None = None


@dataclass(frozen=True)
class TipificacaoInputDTO:
    artigo: str
    descricao: str


@dataclass(frozen=True)
class ItemApreendidoInputDTO:
    """Item apreendido informado já no registro (RF03 — opcional; UC01 cenário alternativo I)."""

    tipo: str  # ARMA_DE_FOGO | ARMA_BRANCA | ENTORPECENTE | VEICULO | VALOR | OBJETO
    descricao: str
    quantidade: int
    estado_conservacao: str  # NOVO | BOM | REGULAR | DANIFICADO | INSERVIVEL
    numero_lacre: str
    localizacao_deposito: str
    unidade: str = "UNIDADE"
    numero_serie: str | None = None
    marca: str | None = None
    calibre: str | None = None


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
    itens_apreendidos: tuple[ItemApreendidoInputDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RegistrarOcorrenciaOutput:
    ocorrencia_id: UUID
    numero_protocolo: str
    status: str
    criada_em: str  # ISO 8601


class InterfaceRegistrarOcorrenciaPolicial(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: RegistrarOcorrenciaInput) -> RegistrarOcorrenciaOutput: ...
