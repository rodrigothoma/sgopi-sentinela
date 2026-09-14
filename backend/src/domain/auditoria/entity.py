"""
Entidade RegistroAuditoria (RF20 / RNF03) — append-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class RegistroAuditoria:
    quem: UUID | None
    quando: datetime
    operacao: str
    entidade: str
    entidade_id: str | None
    dados_antes: dict[str, Any] | None = None
    dados_depois: dict[str, Any] | None = None
    ip: str | None = None
    id: UUID = field(default_factory=uuid4)
