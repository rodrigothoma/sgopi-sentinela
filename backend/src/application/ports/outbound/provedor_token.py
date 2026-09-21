"""Porta de saída: ProvedorToken (RNF02) — emissão/decodificação de token de sessão."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.usuario.entity import Papel


@dataclass(frozen=True)
class DadosToken:
    usuario_id: UUID
    login: str
    papel: Papel
    expira_em: datetime


class ProvedorToken(ABC):
    @abstractmethod
    def emitir(self, usuario_id: UUID, login: str, papel: Papel, agora: datetime) -> tuple[str, datetime]:
        """Devolve (token, expira_em)."""
        ...

    @abstractmethod
    def decodificar(self, token: str, agora: datetime) -> DadosToken:
        """Levanta CredenciaisInvalidasError se inválido/expirado."""
        ...
