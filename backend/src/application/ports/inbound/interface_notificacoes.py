"""Portas de entrada: Gestão de Notificações e Alertas (RF05, RF09, RF10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from application.ports.inbound.ator import Ator
from domain.notificacao.entity import Notificacao


class InterfaceListarNotificacoes(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        apenas_nao_lidas: bool = False,
        limite: int = 50,
    ) -> tuple[list[Notificacao], int]:
        """Retorna lista de notificações do usuário/papel e o total de não lidas."""


class InterfaceMarcarNotificacaoLida(ABC):
    @abstractmethod
    async def executar(self, notificacao_id: UUID, ator: Ator) -> Notificacao:
        """Marca uma notificação individual como lida."""


class InterfaceMarcarTodasLidas(ABC):
    @abstractmethod
    async def executar(self, ator: Ator) -> int:
        """Marca todas as notificações pendentes do usuário como lidas."""


class InterfaceCriarNotificacao(ABC):
    @abstractmethod
    async def executar(
        self,
        *,
        titulo: str,
        mensagem: str,
        tipo: str = "SISTEMA",
        prioridade: str = "MEDIA",
        usuario_id: UUID | None = None,
        papel_destinatario: str | None = None,
        departamento_destinatario: str | None = None,
        link: str | None = None,
        metadados: dict | None = None,
    ) -> Notificacao:
        """Cria e distribui uma notificação via persistência e barramento de eventos."""


# Aliases semânticos para compatibilidade entre camadas
NotificacaoOutput = Notificacao
InterfaceMarcarTodasNotificacoesLidas = InterfaceMarcarTodasLidas


