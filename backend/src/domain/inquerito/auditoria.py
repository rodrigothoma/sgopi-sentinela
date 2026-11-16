"""Eventos de auditoria do inquérito policial (RF06 · RNF03)."""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.inquerito.entity import Inquerito


@dataclass(frozen=True, kw_only=True)
class EventoInquerito(EventoAuditoria):
    """Todo evento do inquérito identifica o número do IP na trilha."""

    ENTIDADE: ClassVar[str] = "inquerito"

    inquerito_id: UUID
    numero: str

    def id_entidade(self) -> str | None:
        return str(self.inquerito_id)

    @abstractmethod
    def _detalhe(self) -> dict[str, Any]: ...

    def dados_depois(self) -> dict[str, Any] | None:
        return {"numero": self.numero, **self._detalhe()}


@dataclass(frozen=True, kw_only=True)
class InqueritoInstaurado(EventoInquerito):
    OPERACAO: ClassVar[str] = "inquerito.instaurar"

    ementa: str
    ocorrencias_vinculadas: tuple[UUID, ...]

    @classmethod
    def de(cls, inquerito: Inquerito) -> Self:
        return cls(
            inquerito_id=inquerito.id,
            numero=inquerito.numero,
            ementa=inquerito.ementa,
            ocorrencias_vinculadas=tuple(inquerito.ocorrencias_ids),
        )

    def _detalhe(self) -> dict[str, Any]:
        return {"ementa": self.ementa, "ocorrencias_vinculadas": [str(x) for x in self.ocorrencias_vinculadas]}


@dataclass(frozen=True, kw_only=True)
class OcorrenciasVinculadasAoInquerito(EventoInquerito):
    OPERACAO: ClassVar[str] = "inquerito.vincular_ocorrencias"

    novas_vinculadas: tuple[UUID, ...]
    total_vinculadas: int

    @classmethod
    def de(cls, inquerito: Inquerito, novas: Iterable[UUID]) -> Self:
        return cls(
            inquerito_id=inquerito.id,
            numero=inquerito.numero,
            novas_vinculadas=tuple(novas),
            total_vinculadas=len(inquerito.ocorrencias_ids),
        )

    def _detalhe(self) -> dict[str, Any]:
        return {"novas_vinculadas": [str(x) for x in self.novas_vinculadas], "total_vinculadas": self.total_vinculadas}


@dataclass(frozen=True, kw_only=True)
class InqueritoConcluido(EventoInquerito):
    OPERACAO: ClassVar[str] = "inquerito.concluir"

    status: str

    @classmethod
    def de(cls, inquerito: Inquerito) -> Self:
        return cls(inquerito_id=inquerito.id, numero=inquerito.numero, status=inquerito.status.value)

    def _detalhe(self) -> dict[str, Any]:
        return {"status": self.status}
