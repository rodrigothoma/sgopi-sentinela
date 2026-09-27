"""Porta de saída: Repositório de Medidas Protetivas (RF09 / UC09)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida


class RepositorioMedidaProtetiva(ABC):
    @abstractmethod
    async def salvar(self, medida: MedidaProtetiva) -> None:
        """Persiste uma medida protetiva."""

    @abstractmethod
    async def buscar_por_id(self, medida_id: UUID) -> MedidaProtetiva | None:
        """Busca medida protetiva por UUID."""

    @abstractmethod
    async def buscar_por_referencia(self, numero_referencia: str) -> MedidaProtetiva | None:
        """Busca medida por número de referência (ex: MP-2026-000001)."""

    @abstractmethod
    async def listar(
        self,
        status: list[StatusMedida] | None = None,
        ocorrencia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MedidaProtetiva], int]:
        """Retorna lista de medidas protetivas e total de registros."""
