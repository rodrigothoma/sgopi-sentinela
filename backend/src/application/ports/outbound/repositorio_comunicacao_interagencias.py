"""Porta de saída: Repositório e Gerador de Ofício para Comunicação Interagências (RF10 / UC10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.interagencias.entity import ComunicacaoInteragencias


class GeradorNumeroOficio(ABC):
    @abstractmethod
    async def proximo_numero(self, ano: int) -> str:
        """Gera o próximo número de ofício no formato OFI-AAAA-NNNNNN."""


class RepositorioComunicacaoInteragencias(ABC):
    @abstractmethod
    async def salvar(self, comunicacao: ComunicacaoInteragencias) -> ComunicacaoInteragencias:
        """Persiste um ofício ou despacho interagências."""

    @abstractmethod
    async def obter_por_id(self, comunicacao_id: UUID) -> ComunicacaoInteragencias | None:
        """Recupera uma comunicação por ID."""

    @abstractmethod
    async def listar(
        self,
        departamento: str | None = None,
        protocolo: str | None = None,
        remetente_id: UUID | None = None,
        limite: int = 50,
    ) -> list[ComunicacaoInteragencias]:
        """Lista comunicações filtradas por departamento (origem/destino), protocolo ou remetente."""

    @abstractmethod
    async def listar_respostas(self, mensagem_pai_id: UUID) -> list[ComunicacaoInteragencias]:
        """Lista todas as respostas vinculadas a um ofício principal (thread)."""
