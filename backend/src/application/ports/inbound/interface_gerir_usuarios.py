"""Porta de entrada: gestão do efetivo pelo Supervisor (sugestão #13 — RNF02). Sem DELETE: desativação lógica."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class UsuarioGestaoOutput:
    """Projeção para a tela de gestão: inclui ``ativo``; nunca ``senha_hash``."""

    id: UUID
    nome: str
    login: str
    papel: str
    ativo: bool


@dataclass(frozen=True)
class CadastrarUsuarioInput:
    nome: str
    login: str
    senha: str
    papel: str


@dataclass(frozen=True)
class AlterarPapelInput:
    usuario_id: UUID
    papel: str


@dataclass(frozen=True)
class AlterarSituacaoUsuarioInput:
    usuario_id: UUID
    motivo: str | None = None


class InterfaceListarUsuariosGestao(ABC):
    @abstractmethod
    async def executar(self, ator: Ator) -> tuple[UsuarioGestaoOutput, ...]: ...


class InterfaceCadastrarUsuario(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: CadastrarUsuarioInput) -> UsuarioGestaoOutput: ...


class InterfaceAlterarPapelUsuario(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AlterarPapelInput) -> UsuarioGestaoOutput: ...


class InterfaceDesativarUsuario(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AlterarSituacaoUsuarioInput) -> UsuarioGestaoOutput: ...


class InterfaceReativarUsuario(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, input_dto: AlterarSituacaoUsuarioInput) -> UsuarioGestaoOutput: ...
