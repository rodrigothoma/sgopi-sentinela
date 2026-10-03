"""Portas de entrada: Inteligência Criminal, Áreas de Risco e Alertas de Criticidade (RF05 / UC05 / UC11)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from application.ports.inbound.ator import Ator


class InterfaceCalcularAreasRisco(ABC):
    @abstractmethod
    async def executar(self, dias: int = 7) -> list[dict]:
        """Calcula clusters e áreas de risco com base nas ocorrências georreferenciadas."""


class InterfaceEmitirAlertaCriticidade(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, dados_alerta: dict) -> dict:
        """Emite formalmente um alerta de criticidade (UC11 / sq11) com gravação de auditoria."""


class InterfaceConfirmarCienciaAlerta(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, alerta_id: str) -> None:
        """Registra no log de auditoria a ciência expressa do Supervisor (UC11)."""
