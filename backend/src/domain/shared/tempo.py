"""
Fuso operacional (puro Python: ``zoneinfo`` é stdlib).

Instantes trafegam em UTC (``Relogio``); datas de calendário — vencimento de medida, "hoje" —
são as do fuso da operação. ``agora.date()`` em UTC erra o dia entre 21h e 24h em Brasília.
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

FUSO_OPERACIONAL = ZoneInfo("America/Sao_Paulo")


def data_operacional(instante: datetime) -> date:
    """Data de calendário do instante no fuso da operação (instante naive é tratado como UTC)."""
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    return instante.astimezone(FUSO_OPERACIONAL).date()
