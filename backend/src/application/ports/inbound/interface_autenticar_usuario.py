"""Porta de entrada: InterfaceAutenticarUsuario (RF11)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AutenticarInput:
    login: str
    senha: str
    ip: str | None = None


@dataclass(frozen=True)
class UsuarioOutput:
    id: UUID
    nome: str
    login: str
    papel: str


@dataclass(frozen=True)
class AutenticarOutput:
    access_token: str
    token_type: str
    expira_em: str  # ISO 8601
    usuario: UsuarioOutput


class InterfaceAutenticarUsuario(ABC):
    @abstractmethod
    async def executar(self, input_dto: AutenticarInput) -> AutenticarOutput: ...
