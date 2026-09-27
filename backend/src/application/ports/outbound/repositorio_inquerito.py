"""Porta de saída: Repositório de Inquéritos Policiais (RF06 / UC06)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.inquerito.entity import Inquerito, StatusInquerito


class RepositorioInquerito(ABC):
    @abstractmethod
    async def salvar(self, inquerito: Inquerito) -> None:
        """Persiste um inquérito (criação ou atualização)."""

    @abstractmethod
    async def buscar_por_id(self, inquerito_id: UUID) -> Inquerito | None:
        """Busca inquérito por UUID."""

    @abstractmethod
    async def buscar_por_numero(self, numero: str) -> Inquerito | None:
        """Busca inquérito por número formal (ex: IP-2026-000001)."""

    @abstractmethod
    async def listar(
        self,
        status: list[StatusInquerito] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Inquerito], int]:
        """Retorna lista de inquéritos e total de registros."""
