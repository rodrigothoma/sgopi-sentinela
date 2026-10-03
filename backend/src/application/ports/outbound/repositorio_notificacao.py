"""Porta de saída: Repositório de Notificações e Alertas (RF05, RF09, RF10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from domain.notificacao.entity import Notificacao


class RepositorioNotificacao(ABC):
    @abstractmethod
    async def salvar(self, notificacao: Notificacao) -> Notificacao:
        """Persiste ou atualiza uma notificação."""

    @abstractmethod
    async def obter_por_id(self, notificacao_id: UUID) -> Notificacao | None:
        """Recupera uma notificação pelo seu UUID primário."""

    @abstractmethod
    async def listar(
        self,
        usuario_id: UUID | None = None,
        papel: str | None = None,
        apenas_nao_lidas: bool = False,
        limite: int = 50,
    ) -> list[Notificacao]:
        """Lista notificações destinadas ao usuário específico, ao seu papel ou de difusão geral."""

    @abstractmethod
    async def contar_nao_lidas(self, usuario_id: UUID | None = None, papel: str | None = None) -> int:
        """Retorna o número de notificações pendentes de leitura para o usuário."""

    @abstractmethod
    async def marcar_todas_lidas(self, usuario_id: UUID | None, papel: str | None, instante: datetime) -> int:
        """Marca como lidas todas as notificações do usuário ou papel."""
