"""Porta de entrada: listagem do efetivo (RF12) — consumida pela tela inicial."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class UsuarioOutput:
    """Projeção pública do usuário: nunca expõe ``senha_hash``."""

    id: UUID
    nome: str
    login: str
    papel: str


class InterfaceListarUsuarios(ABC):
    @abstractmethod
    async def executar(self, ator: Ator) -> tuple[UsuarioOutput, ...]: ...
