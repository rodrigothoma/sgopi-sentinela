"""Porta de saída: RepositorioOrdemDespacho (RF18)."""
from abc import ABC, abstractmethod
from uuid import UUID

from domain.despacho.entity import OrdemDeDespacho


class RepositorioOrdemDespacho(ABC):
    @abstractmethod
    async def salvar(self, ordem: OrdemDeDespacho) -> None: ...

    @abstractmethod
    async def buscar_por_id(self, ordem_id: UUID) -> OrdemDeDespacho | None: ...

    @abstractmethod
    async def listar(self, ocorrencia_id: UUID | None = None, somente_ativas: bool = False, limit: int = 100) -> list[OrdemDeDespacho]:
        """Mais recente primeiro."""
        ...
