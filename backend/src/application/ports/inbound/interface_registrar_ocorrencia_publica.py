"""
Porta de entrada: InterfaceRegistrarOcorrenciaPublica (RF01 — Delegacia Online).

O cidadão comunica o fato sem autenticação; o caso de uso aplica as regras do canal
público, registra em nome do ator de sistema CIDADAO (nunca de um policial real) e
delega o registro ao caso de uso de RF01.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RegistrarOcorrenciaPublicaInput:
    nome_solicitante: str
    documento: str
    email: str
    telefone: str
    declaracao_maioridade: bool
    natureza: str
    descricao: str
    localizacao: str
    latitude: float
    longitude: float
    data_hora_fato: datetime
    ip: str | None = None


@dataclass(frozen=True)
class RegistrarOcorrenciaPublicaOutput:
    ocorrencia_id: UUID
    numero_protocolo: str
    status: str
    criada_em: str  # ISO 8601
    # Exibido uma única vez ao cidadão; só o hash é persistido
    codigo_acompanhamento: str


class InterfaceRegistrarOcorrenciaPublica(ABC):
    @abstractmethod
    async def executar(self, input_dto: RegistrarOcorrenciaPublicaInput) -> RegistrarOcorrenciaPublicaOutput: ...
