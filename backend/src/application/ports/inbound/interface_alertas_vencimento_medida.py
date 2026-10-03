"""Portas de entrada: Alertas de Vencimento de Medida Protetiva (RF09 / UC12)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from application.ports.inbound.ator import Ator


class InterfaceEmitirAlertaVencimentoMedida(ABC):
    @abstractmethod
    async def executar(
        self,
        ator: Ator,
        medida_id: UUID | None = None,
        email_destinatario_customizado: str | None = None,
    ) -> dict:
        """Dispara alerta de vencimento de medida (manual por medida_id ou automático em lote)."""
