"""Porta de saída: RepositorioViatura (RF02)."""
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
        """Somente cadastros ativos, ordenados por prefixo; buscas por identidade preservam o histórico."""
        ...
