"""Porta de saída: Repositório de Laudos Periciais (RF07 / UC07)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.laudo.entity import LaudoPericial, StatusLaudo


class RepositorioLaudoPericial(ABC):
    @abstractmethod
    async def salvar(self, laudo: LaudoPericial) -> None:
        """Persiste um laudo pericial."""

    @abstractmethod
    async def buscar_por_id(self, laudo_id: UUID) -> LaudoPericial | None:
        """Busca laudo por UUID."""

    @abstractmethod
    async def buscar_por_referencia(self, numero_referencia: str) -> LaudoPericial | None:
        """Busca laudo por número de referência (ex: LP-2026-000001)."""

    @abstractmethod
    async def listar(
        self,
        status: list[StatusLaudo] | None = None,
        ocorrencia_id: UUID | None = None,
        inquerito_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LaudoPericial], int]:
        """Retorna lista de laudos e total de registros."""
