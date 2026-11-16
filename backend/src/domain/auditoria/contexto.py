"""Contexto de um registro de auditoria: quem agiu, quando e de onde (RNF03)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ContextoAuditoria:
    """Separado do evento (o que aconteceu): o mesmo evento pode ocorrer por um usuário,
    pelo cidadão sem login (``quem`` nulo) ou por um processo do sistema."""

    quem: UUID | None
    quando: datetime
    ip: str | None = None
