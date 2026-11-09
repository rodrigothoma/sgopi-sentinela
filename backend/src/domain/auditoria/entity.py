"""
Entidade RegistroAuditoria (RNF03) — append-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from domain.auditoria.catalogo import EntidadeAuditada, OperacaoAuditada


@dataclass(frozen=True)
class RegistroAuditoria:
    """Entrada imutável da trilha; ``operacao``/``entidade`` vêm do catálogo e são guardadas como texto."""

    quem: UUID | None
    quando: datetime
    operacao: OperacaoAuditada | str
    entidade: EntidadeAuditada | str
    entidade_id: str | None
    dados_antes: dict[str, Any] | None = None
    dados_depois: dict[str, Any] | None = None
    ip: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        # Persistência, filtros e JSON trabalham com o texto puro, nunca com o membro do enum.
        for campo in ("operacao", "entidade"):
            valor = getattr(self, campo)
            if isinstance(valor, Enum):
                object.__setattr__(self, campo, valor.value)
