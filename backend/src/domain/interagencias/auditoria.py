"""Eventos de auditoria dos ofícios interagências (RF10 · RNF03)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Self
from uuid import UUID

from domain.auditoria.evento import EventoAuditoria
from domain.interagencias.entity import ComunicacaoInteragencias


@dataclass(frozen=True, kw_only=True)
class EventoComunicacao(EventoAuditoria):
    ENTIDADE: ClassVar[str] = "comunicacoes_interagencias"

    comunicacao_id: UUID
    numero_oficio: str

    def id_entidade(self) -> str | None:
        return str(self.comunicacao_id)


@dataclass(frozen=True, kw_only=True)
class OficioEnviado(EventoComunicacao):
    OPERACAO: ClassVar[str] = "interagencias.enviar"
    GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("ENVIO_COMUNICACAO_INTERAGENCIAS",)

    origem: str
    destinatarios: tuple[str, ...]
    assunto: str
    protocolo: str | None

    @classmethod
    def de(cls, oficio: ComunicacaoInteragencias) -> Self:
        return cls(
            comunicacao_id=oficio.id,
            numero_oficio=oficio.numero_oficio,
            origem=oficio.departamento_origem,
            destinatarios=tuple(oficio.departamentos_destinatarios),
            assunto=oficio.assunto,
            protocolo=oficio.protocolo_ocorrencia,
        )

    def dados_depois(self) -> dict[str, Any] | None:
        return {
            "numero_oficio": self.numero_oficio,
            "origem": self.origem,
            "destinatarios": list(self.destinatarios),
            "assunto": self.assunto,
            "protocolo": self.protocolo,
        }


@dataclass(frozen=True, kw_only=True)
class OficioRespondido(EventoComunicacao):
    OPERACAO: ClassVar[str] = "interagencias.responder"
    GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("RESPOSTA_COMUNICACAO_INTERAGENCIAS",)

    mensagem_pai_id: UUID

    @classmethod
    def de(cls, resposta: ComunicacaoInteragencias) -> Self:
        if resposta.mensagem_pai_id is None:
            raise ValueError("Resposta sem ofício de origem (mensagem_pai_id).")
        return cls(comunicacao_id=resposta.id, numero_oficio=resposta.numero_oficio, mensagem_pai_id=resposta.mensagem_pai_id)

    def dados_depois(self) -> dict[str, Any] | None:
        return {"mensagem_pai_id": str(self.mensagem_pai_id), "numero_oficio": self.numero_oficio}
