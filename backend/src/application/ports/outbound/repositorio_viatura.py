"""Porta de saída: RepositorioViatura (RF15)."""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.viatura.entity import SituacaoViatura, Viatura


class RepositorioViatura(ABC):
    @abstractmethod
    async def salvar(self, viatura: Viatura) -> None: ...

    @abstractmethod
    async def buscar_por_id(self, viatura_id: UUID) -> Viatura | None: ...

    @abstractmethod
    async def buscar_por_prefixo(self, prefixo: str) -> Viatura | None: ...

    @abstractmethod
    async def buscar_por_placa(self, placa: str) -> Viatura | None: ...

    @abstractmethod
    async def listar(self, situacoes: tuple[SituacaoViatura, ...] = ()) -> list[Viatura]:
        """Ordenada por prefixo."""
        ...
