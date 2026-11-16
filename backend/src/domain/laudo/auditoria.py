"""Eventos de auditoria do laudo pericial (RF07 · RNF03)."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.laudo.entity import LaudoPericial


@dataclass(frozen=True, kw_only=True)
class EventoLaudo(EventoAuditoria):
    """Todo evento do laudo identifica o número de referência na trilha."""

    ENTIDADE: ClassVar[str] = "laudo_pericial"

    laudo_id: UUID
    numero_referencia: str

    def id_entidade(self) -> str | None:
        return str(self.laudo_id)

    @abstractmethod
    def _detalhe(self) -> dict[str, Any]: ...

    def dados_depois(self) -> dict[str, Any] | None:
        return {"numero_referencia": self.numero_referencia, **self._detalhe()}


@dataclass(frozen=True, kw_only=True)
class LaudoSolicitado(EventoLaudo):
    OPERACAO: ClassVar[str] = "laudo.solicitar"

    tipo_pericia: str
    ocorrencia_id: UUID | None
    inquerito_id: UUID | None

    @classmethod
    def de(cls, laudo: LaudoPericial) -> Self:
        return cls(
            laudo_id=laudo.id,
            numero_referencia=laudo.numero_referencia,
            tipo_pericia=laudo.tipo_pericia.value,
            ocorrencia_id=laudo.ocorrencia_id,
            inquerito_id=laudo.inquerito_id,
        )

    def _detalhe(self) -> dict[str, Any]:
        return {
            "tipo_pericia": self.tipo_pericia,
            "ocorrencia_id": str(self.ocorrencia_id) if self.ocorrencia_id else None,
            "inquerito_id": str(self.inquerito_id) if self.inquerito_id else None,
        }


@dataclass(frozen=True, kw_only=True)
class LaudoAnexado(EventoLaudo):
    OPERACAO: ClassVar[str] = "laudo.anexar"

    arquivo_nome: str | None
    hash_sha256: str | None
    status: str

    @classmethod
    def de(cls, laudo: LaudoPericial) -> Self:
        return cls(
            laudo_id=laudo.id,
            numero_referencia=laudo.numero_referencia,
            arquivo_nome=laudo.arquivo_nome,
            hash_sha256=laudo.hash_sha256,
            status=laudo.status.value,
        )

    def _detalhe(self) -> dict[str, Any]:
        return {"arquivo_nome": self.arquivo_nome, "hash_sha256": self.hash_sha256, "status": self.status}


@dataclass(frozen=True, kw_only=True)
class LaudoBaixado(EventoLaudo):
    """Download do arquivo homologado, com o resultado da conferência de integridade."""

    OPERACAO: ClassVar[str] = "laudo.download"

    integridade: str

    @classmethod
    def de(cls, laudo: LaudoPericial, integridade: str) -> Self:
        return cls(laudo_id=laudo.id, numero_referencia=laudo.numero_referencia, integridade=integridade)

    def _detalhe(self) -> dict[str, Any]:
        return {"integridade": self.integridade}
