"""Eventos de despacho (RF17)."""
from datetime import datetime

from domain.despacho.entity import OrdemDeDespacho
from domain.shared.eventos import EventoDominio


def ordem_de_despacho_criada(ordem: OrdemDeDespacho, em: datetime, **extra: object) -> EventoDominio:
    return EventoDominio(
        tipo="OrdemDeDespachoCriada",
        ocorrido_em=em,
        dados={"ordem_id": str(ordem.id), "numero": ordem.numero, "ocorrencia_id": str(ordem.ocorrencia_id), "viatura_id": str(ordem.viatura_id), **extra},
    )
