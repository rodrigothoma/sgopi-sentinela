"""
Adapter de entrada HTTP: /v1/notificacoes (RF09 / UC12 / UC13).

Central de Notificações in-app com suporte a contagem de não lidas e atualização de status de leitura.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from adapters.inbound.http.deps import ator_atual
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_notificacoes import (
    InterfaceListarNotificacoes,
    InterfaceMarcarNotificacaoLida,
    InterfaceMarcarTodasNotificacoesLidas,
    NotificacaoOutput,
)
from infrastructure.di import (
    get_listar_notificacoes,
    get_marcar_notificacao_lida,
    get_marcar_todas_notificacoes_lidas,
)

router = APIRouter(prefix="/v1/notificacoes", tags=["notificacoes"])


class NotificacaoSchema(BaseModel):
    id: UUID
    usuario_id: UUID | None = None
    papel_destinatario: str | None = None
    departamento_destinatario: str | None = None
    titulo: str
    mensagem: str
    tipo: str
    prioridade: str
    link: str | None = None
    lida: bool
    lida_em: str | None = None
    criada_em: str


class ListaNotificacoesResponse(BaseModel):
    itens: list[NotificacaoSchema]
    total: int
    nao_lidas: int
    limit: int
    offset: int


class ResumoNotificacoesResponse(BaseModel):
    nao_lidas: int


class MarcarTodasLidasResponse(BaseModel):
    atualizadas: int


def _para_schema(out: NotificacaoOutput) -> NotificacaoSchema:
    return NotificacaoSchema(
        id=out.id,
        usuario_id=out.usuario_id,
        papel_destinatario=out.papel_destinatario,
        departamento_destinatario=out.departamento_destinatario,
        titulo=out.titulo,
        mensagem=out.mensagem,
        tipo=out.tipo.value if hasattr(out.tipo, "value") else str(out.tipo),
        prioridade=out.prioridade.value if hasattr(out.prioridade, "value") else str(out.prioridade),
        link=out.link,
        lida=out.lida,
        lida_em=out.lida_em.isoformat() if out.lida_em else None,
        criada_em=out.criada_em.isoformat(),
    )


@router.get("", response_model=ListaNotificacoesResponse)
async def listar_notificacoes(
    apenas_nao_lidas: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ator: Ator = Depends(ator_atual),
    uc: InterfaceListarNotificacoes = Depends(get_listar_notificacoes),
) -> ListaNotificacoesResponse:
    """Lista notificações do usuário logado, com filtros e contagem de pendências."""
    itens, nao_lidas = await uc.executar(
        ator=ator,
        apenas_nao_lidas=apenas_nao_lidas,
        limite=limit,
        offset=offset,
    )
    return ListaNotificacoesResponse(
        itens=[_para_schema(i) for i in itens],
        total=len(itens),  # itens desta página; o total pendente vem em ``nao_lidas``
        nao_lidas=nao_lidas,
        limit=limit,
        offset=offset,
    )


@router.get("/resumo", response_model=ResumoNotificacoesResponse)
async def obter_resumo(
    ator: Ator = Depends(ator_atual),
    uc: InterfaceListarNotificacoes = Depends(get_listar_notificacoes),
) -> ResumoNotificacoesResponse:
    """Retorna apenas o contador de notificações não lidas para o badge do sininho."""
    _, nao_lidas = await uc.executar(ator=ator, apenas_nao_lidas=True, limite=1)
    return ResumoNotificacoesResponse(nao_lidas=nao_lidas)


@router.patch("/{notificacao_id}/lida", response_model=NotificacaoSchema)
async def marcar_como_lida(
    notificacao_id: UUID,
    ator: Ator = Depends(ator_atual),
    uc: InterfaceMarcarNotificacaoLida = Depends(get_marcar_notificacao_lida),
) -> NotificacaoSchema:
    """Marca uma notificação individual como lida."""
    res = await uc.executar(notificacao_id=notificacao_id, ator=ator)
    return _para_schema(res)


@router.post("/marcar-todas-lidas", response_model=MarcarTodasLidasResponse)
async def marcar_todas_como_lidas(
    ator: Ator = Depends(ator_atual),
    uc: InterfaceMarcarTodasNotificacoesLidas = Depends(get_marcar_todas_notificacoes_lidas),
) -> MarcarTodasLidasResponse:
    """Marca todas as notificações pendentes do usuário como lidas."""
    atualizadas = await uc.executar(ator=ator)
    return MarcarTodasLidasResponse(atualizadas=atualizadas)
