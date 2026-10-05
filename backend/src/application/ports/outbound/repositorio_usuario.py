"""Porta de saída: RepositorioUsuario (RNF02)."""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.usuario.entity import Usuario


class RepositorioUsuario(ABC):
    @abstractmethod
    async def buscar_por_login(self, login: str) -> Usuario | None: ...

    @abstractmethod
    async def buscar_por_id(self, usuario_id: UUID) -> Usuario | None: ...

    @abstractmethod
    async def salvar(self, usuario: Usuario) -> None: ...

    @abstractmethod
    async def listar(self) -> list[Usuario]: ...
