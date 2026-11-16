"""Porta de entrada: catálogo das ações auditadas (RNF03), para filtros da trilha."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from application.ports.inbound.ator import Ator


@dataclass(frozen=True)
class AcaoAuditadaOutput:
    operacao: str
    entidade: str


class InterfaceListarCatalogoAuditoria(ABC):
    @abstractmethod
    async def executar(self, ator: Ator) -> tuple[AcaoAuditadaOutput, ...]:
        """Todas as ações que podem aparecer na trilha, geradas das classes de evento."""
