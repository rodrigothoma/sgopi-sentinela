"""Eventos de auditoria dos alertas de criticidade da inteligência criminal (RF05/UC11 · RNF03)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria


@dataclass(frozen=True, kw_only=True)
class AlertaCriticidadeEmitido(EventoAuditoria):
    OPERACAO: ClassVar[str] = "inteligencia.emitir_alerta"
    ENTIDADE: ClassVar[str] = "inteligencia_criminal"
    GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("EMISSAO_ALERTA_CRITICIDADE",)

    notificacao_id: UUID
    dados_alerta: dict[str, Any]

    def id_entidade(self) -> str | None:
        return str(self.notificacao_id)

    def dados_depois(self) -> dict[str, Any] | None:
        return dict(self.dados_alerta)


@dataclass(frozen=True, kw_only=True)
class CienciaAlertaRegistrada(EventoAuditoria):
    """Supervisão confirmou a leitura do alerta de criticidade."""

    OPERACAO: ClassVar[str] = "inteligencia.registrar_ciencia"
    ENTIDADE: ClassVar[str] = "notificacoes"
    GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("CIENCIA_ALERTA_CRITICIDADE",)

    notificacao_id: UUID
    supervisor: str
    papel: str

    def id_entidade(self) -> str | None:
        return str(self.notificacao_id)

    def dados_depois(self) -> dict[str, Any] | None:
        return {"supervisor": self.supervisor, "papel": self.papel}
