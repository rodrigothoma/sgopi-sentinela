"""Eventos de auditoria do despacho tático (RF02 · RNF03)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.despacho.entity import OrdemDeDespacho
from domain.viatura.entity import Viatura


@dataclass(frozen=True, kw_only=True)
class OrdemDeDespachoCriada(EventoAuditoria):
    OPERACAO: ClassVar[str] = "despacho.criar"
    ENTIDADE: ClassVar[str] = "OrdemDeDespacho"
    ENTIDADE_GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("ordens_despacho",)

    ordem_id: UUID
    numero: str
    ocorrencia_id: UUID
    viatura_id: UUID
    prefixo: str
    apoio: bool

    @classmethod
    def de(cls, ordem: OrdemDeDespacho, viatura: Viatura) -> Self:
        return cls(
            ordem_id=ordem.id,
            numero=ordem.numero,
            ocorrencia_id=ordem.ocorrencia_id,
            viatura_id=viatura.id,
            prefixo=viatura.prefixo,
            apoio=ordem.apoio,
        )

    def id_entidade(self) -> str | None:
        return str(self.ordem_id)

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "numero": self.numero,
            "ocorrencia_id": str(self.ocorrencia_id),
            "viatura_id": str(self.viatura_id),
            "prefixo": self.prefixo,
            "apoio": self.apoio,
        }
