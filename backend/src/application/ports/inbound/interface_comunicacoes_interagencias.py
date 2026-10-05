"""Portas de entrada: Comunicações Interagências (RF10 / UC10)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from application.ports.inbound.ator import Ator
from domain.interagencias.entity import ComunicacaoInteragencias


class InterfaceEnviarComunicacaoInteragencias(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        departamento_origem: str,
        departamentos_destinatarios: list[str],
        assunto: str,
        corpo: str,
        protocolo_ocorrencia: str | None = None,
        nivel_sigilo: str = "PADRAO",
        prioridade: str = "MEDIA",
    ) -> ComunicacaoInteragencias:
        """Emite formalmente um ofício interagências vinculado ou não a protocolo de ocorrência."""


class InterfaceConsultarComunicacoesInteragencias(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        departamento: str | None = None,
        protocolo: str | None = None,
    ) -> list[ComunicacaoInteragencias]:
        """Consulta comunicações interagências na caixa de entrada/saída."""


class InterfaceResponderComunicacaoInteragencias(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        mensagem_pai_id: UUID,
        departamento_origem: str,
        assunto: str,
        corpo: str,
        prioridade: str = "MEDIA",
    ) -> ComunicacaoInteragencias:
        """Responde formalmente a uma comunicação anterior (thread)."""
