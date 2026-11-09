"""Porta de saída: Repositório e Gerador de Ofício para Comunicação Interagências (RF10 / UC10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Collection
from uuid import UUID

from domain.interagencias.entity import ComunicacaoInteragencias, NivelSigilo


class GeradorNumeroOficio(ABC):
    @abstractmethod
    async def proximo_numero(self, ano: int) -> str:
        """Gera o próximo número de ofício no formato OFI-AAAA-NNNNNN."""


def formatar_numero_oficio(ano: int, sequencial: int) -> str:
    return f"OFI-{ano:04d}-{sequencial:06d}"


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
        niveis_sigilo: Collection[NivelSigilo] | None = None,
        visivel_ao_usuario: UUID | None = None,
    ) -> list[ComunicacaoInteragencias]:
        """Lista as comunicações mais recentes, até ``limite``, aplicando todos os filtros no banco.

        ``departamento`` casa com a origem ou com qualquer destinatário. Com ``niveis_sigilo``,
        só entram ofícios desses níveis, exceto os enviados por ``visivel_ao_usuario``, que
        o remetente sempre vê.
        """

    @abstractmethod
    async def listar_respostas(self, mensagem_pai_id: UUID) -> list[ComunicacaoInteragencias]:
        """Lista todas as respostas vinculadas a um ofício principal (thread)."""
