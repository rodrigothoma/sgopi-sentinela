"""Porta de entrada: linha do tempo unificada da ocorrência (sugestão #12 — RF01 / RNF03)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from application.ports.inbound.ator import Ator


class TipoEventoLinhaDoTempo(str, Enum):
    STATUS = "STATUS"
    DESPACHO = "DESPACHO"
    ORDEM_ENCERRADA = "ORDEM_ENCERRADA"
    EVIDENCIA_ANEXADA = "EVIDENCIA_ANEXADA"
    INTEGRIDADE_VERIFICADA = "INTEGRIDADE_VERIFICADA"
    ITEM_APREENDIDO = "ITEM_APREENDIDO"
    CUSTODIA_MOVIMENTADA = "CUSTODIA_MOVIMENTADA"
    INQUERITO_VINCULADO = "INQUERITO_VINCULADO"
    LAUDO_SOLICITADO = "LAUDO_SOLICITADO"
    LAUDO_CONCLUIDO = "LAUDO_CONCLUIDO"


@dataclass(frozen=True)
class EventoLinhaDoTempoOutput:
    em: str  # ISO 8601
    tipo: TipoEventoLinhaDoTempo
    por_id: UUID | None = None
    por_nome: str | None = None
    # Dados próprios de cada tipo (ex.: de/para do status, número da ordem, lacre do item)
    detalhes: dict[str, Any] = field(default_factory=dict)


class InterfaceLinhaDoTempo(ABC):
    @abstractmethod
    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> tuple[EventoLinhaDoTempoOutput, ...]:
        """Eventos em ordem cronológica; mesma política de acesso do detalhe da ocorrência."""
        ...
