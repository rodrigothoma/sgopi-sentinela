"""Eventos de auditoria da medida protetiva (RF09 · RNF03)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.medida_protetiva.entity import MedidaProtetiva


@dataclass(frozen=True, kw_only=True)
class EventoMedida(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "medida_protetiva"
    ENTIDADE_GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("medidas_protetivas",)

    medida_id: UUID

    def id_entidade(self) -> str | None:
        return str(self.medida_id)


@dataclass(frozen=True, kw_only=True)
class MedidaConcedida(EventoMedida):
    OPERACAO: ClassVar[str] = "medida_protetiva.conceder"

    numero_referencia: str
    ocorrencia_id: UUID
    vitima_id: UUID
    agressor_id: UUID
    tipos_restricao: tuple[str, ...]
    prazo_dias: int
    data_vencimento: date

    @classmethod
    def de(cls, medida: MedidaProtetiva) -> Self:
        return cls(
            medida_id=medida.id,
            numero_referencia=medida.numero_referencia,
            ocorrencia_id=medida.ocorrencia_id,
            vitima_id=medida.vitima_id,
            agressor_id=medida.agressor_id,
            tipos_restricao=tuple(medida.tipos_restricao),
            prazo_dias=medida.prazo_dias,
            data_vencimento=medida.data_vencimento,
        )

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "numero_referencia": self.numero_referencia,
            "ocorrencia_id": str(self.ocorrencia_id),
            "vitima_id": str(self.vitima_id),
            "agressor_id": str(self.agressor_id),
            "tipos_restricao": list(self.tipos_restricao),
            "prazo_dias": self.prazo_dias,
            "data_vencimento": self.data_vencimento.isoformat(),
        }


@dataclass(frozen=True, kw_only=True)
class MedidaRenovada(EventoMedida):
    OPERACAO: ClassVar[str] = "medida_protetiva.renovar"

    vencimento_anterior: date
    prazo_anterior: int
    data_vencimento: date
    prazo_dias: int
    dias_adicionais: int
    justificativa: str

    @classmethod
    def de(cls, medida: MedidaProtetiva, vencimento_anterior: date, dias_adicionais: int, justificativa: str) -> Self:
        return cls(
            medida_id=medida.id,
            vencimento_anterior=vencimento_anterior,
            prazo_anterior=medida.prazo_dias - dias_adicionais,
            data_vencimento=medida.data_vencimento,
            prazo_dias=medida.prazo_dias,
            dias_adicionais=dias_adicionais,
            justificativa=justificativa,
        )

    def dados_antes(self) -> dict[str, Any] | None:
        return {"data_vencimento": self.vencimento_anterior.isoformat(), "prazo_dias": self.prazo_anterior}

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "data_vencimento": self.data_vencimento.isoformat(),
            "prazo_dias": self.prazo_dias,
            "dias_adicionais": self.dias_adicionais,
            "justificativa": self.justificativa,
        }


@dataclass(frozen=True, kw_only=True)
class MedidaRevogada(EventoMedida):
    OPERACAO: ClassVar[str] = "medida_protetiva.revogar"

    status_antes: str
    status: str
    motivo: str

    @classmethod
    def de(cls, medida: MedidaProtetiva, status_anterior: str, motivo: str) -> Self:
        return cls(medida_id=medida.id, status_antes=status_anterior, status=medida.status.value, motivo=motivo)

    def dados_antes(self) -> dict[str, Any] | None:
        return {"status": self.status_antes}

    def dados_depois(self) -> dict[str, Any] | None:
        return {"status": self.status, "motivo_revogacao": self.motivo}


@dataclass(frozen=True, kw_only=True)
class AlertaVencimentoEmitido(EventoMedida):
    """Alerta do UC12 (e-mail à vítima e notificação ao Delegado), automático ou manual."""

    OPERACAO: ClassVar[str] = "medida_protetiva.alertar_vencimento"
    GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("ALERTA_VENCIMENTO_MEDIDA",)

    numero_referencia: str
    dias_restantes: int
    email_destinatario: str | None
    email_enviado: bool
    manual: bool

    @classmethod
    def de(cls, medida: MedidaProtetiva, dias_restantes: int, email_destinatario: str | None, email_enviado: bool, manual: bool) -> Self:
        return cls(
            medida_id=medida.id,
            numero_referencia=medida.numero_referencia,
            dias_restantes=dias_restantes,
            email_destinatario=email_destinatario,
            email_enviado=email_enviado,
            manual=manual,
        )

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "numero_referencia": self.numero_referencia,
            "dias_restantes": self.dias_restantes,
            "email_destinatario": self.email_destinatario,
            "email_enviado": self.email_enviado,
            "manual": self.manual,
        }
