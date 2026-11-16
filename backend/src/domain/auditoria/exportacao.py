"""Eventos de auditoria de exportação de dados (RNF03): a própria exportação entra na trilha."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from domain.auditoria.evento import EventoAuditoria


@dataclass(frozen=True, kw_only=True)
class ExportacaoRealizada(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "Exportacao"
    RECURSO: ClassVar[str]

    formato: str
    filtros: dict[str, Any]
    total_linhas: int

    def id_entidade(self) -> str | None:
        return self.RECURSO

    def dados_depois(self) -> dict[str, Any] | None:
        return {"formato": self.formato, "filtros": self.filtros, "total_linhas": self.total_linhas}


@dataclass(frozen=True, kw_only=True)
class ExportacaoOcorrencias(ExportacaoRealizada):
    OPERACAO: ClassVar[str] = "ocorrencias.exportar"
    RECURSO: ClassVar[str] = "ocorrencias"


@dataclass(frozen=True, kw_only=True)
class ExportacaoAuditoria(ExportacaoRealizada):
    OPERACAO: ClassVar[str] = "auditoria.exportar"
    RECURSO: ClassVar[str] = "auditoria"


_POR_RECURSO: dict[str, type[ExportacaoRealizada]] = {c.RECURSO: c for c in (ExportacaoOcorrencias, ExportacaoAuditoria)}


def exportacao_de(recurso: str, formato: str, filtros: dict[str, Any], total_linhas: int) -> ExportacaoRealizada:
    """Evento da exportação do ``recurso`` (``ocorrencias`` ou ``auditoria``)."""
    return _POR_RECURSO[recurso](formato=formato, filtros=filtros, total_linhas=total_linhas)
