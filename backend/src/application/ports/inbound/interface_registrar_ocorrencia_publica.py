"""
Porta de entrada: InterfaceRegistrarOcorrenciaPublica (RF01 — Delegacia Online).

O cidadão comunica o fato sem autenticação; o caso de uso aplica as regras do canal
público e delega o registro ao caso de uso de RF01.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import RegistrarOcorrenciaOutput


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


class InterfaceRegistrarOcorrenciaPublica(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: RegistrarOcorrenciaPublicaInput) -> RegistrarOcorrenciaOutput: ...
