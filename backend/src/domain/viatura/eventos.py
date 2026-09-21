"""Eventos de domínio de viatura (consumidos por tempo real / RF02 e RNF01)."""
from datetime import datetime

from domain.shared.eventos import EventoDominio
from domain.viatura.entity import Viatura


def _dados(v: Viatura) -> dict:
    p = v.ultima_posicao
    return {
        "viatura_id": str(v.id),
        "prefixo": v.prefixo,
        "situacao": v.situacao.value,
        "latitude": p.coordenada.latitude if p else None,
        "longitude": p.coordenada.longitude if p else None,
        "registrada_em": p.registrada_em.isoformat() if p else None,
    }


def posicao_atualizada(v: Viatura, em: datetime) -> EventoDominio:
    return EventoDominio(tipo="PosicaoAtualizada", ocorrido_em=em, dados=_dados(v))


def viatura_situacao_alterada(v: Viatura, em: datetime, **extra: object) -> EventoDominio:
    return EventoDominio(tipo="ViaturaSituacaoAlterada", ocorrido_em=em, dados={**_dados(v), **extra})
