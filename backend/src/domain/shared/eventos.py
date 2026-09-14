"""
Evento de domínio base. Casos de uso publicam eventos pela porta PublicadorEventos;
adapters (WebSocket, broker) fazem o fan-out. Puro Python.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    ocorrido_em: datetime
    dados: dict[str, Any] = field(default_factory=dict)
