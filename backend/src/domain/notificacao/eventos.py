"""Evento de tempo real emitido quando uma notificação é persistida (fan-out filtrado por destinatário)."""
from __future__ import annotations

from domain.notificacao.entity import Notificacao
from domain.shared.eventos import EventoDominio

NOTIFICACAO_EMITIDA = "NOTIFICACAO_EMITIDA"


def notificacao_emitida(notificacao: Notificacao) -> EventoDominio:
    """Carrega ``usuario_id``/``papel_destinatario`` para que o WebSocket entregue só ao destinatário."""
    return EventoDominio(
        tipo=NOTIFICACAO_EMITIDA,
        ocorrido_em=notificacao.criada_em,
        dados={
            "id": str(notificacao.id),
            "titulo": notificacao.titulo,
            "mensagem": notificacao.mensagem,
            "tipo": notificacao.tipo.value,
            "prioridade": notificacao.prioridade.value,
            "usuario_id": str(notificacao.usuario_id) if notificacao.usuario_id else None,
            "papel_destinatario": notificacao.papel_destinatario,
            "departamento_destinatario": notificacao.departamento_destinatario,
            "link": notificacao.link,
            "criada_em": notificacao.criada_em.isoformat(),
        },
    )
