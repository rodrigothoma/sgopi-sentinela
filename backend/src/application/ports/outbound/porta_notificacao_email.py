"""Porta de saída: Envio de e-mail de notificação e alertas (RF09 / UC12)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class PortaNotificacaoEmail(ABC):
    @abstractmethod
    async def enviar_email(self, para: str, assunto: str, corpo_html: str, corpo_texto: str) -> bool:
        """Dispara mensagem de e-mail institucional para o destinatário."""
