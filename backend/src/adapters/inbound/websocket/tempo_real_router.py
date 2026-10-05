"""
WS /v1/tempo-real (RF02 / RNF01).

Navegadores não enviam headers customizados no handshake; o token vai no cabeçalho
``Sec-WebSocket-Protocol`` como ``["sgopi.bearer", <jwt>]`` — nunca na URL, que
acaba em logs de acesso, proxies e histórico. O servidor responde só ``sgopi.bearer``.

O ``Origin`` do navegador precisa estar na lista do CORS (bloqueia Cross-Site WebSocket
Hijacking); clientes sem ``Origin`` (scripts, testes) seguem só com o token. A cada mensagem
do cliente (keep-alive) a expiração do token é reavaliada.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from adapters.inbound.http.deps import exigir_usuario_ativo, extrair_sessao
from adapters.inbound.websocket.gerenciador_conexoes import CODIGO_POLITICA_VIOLADA, Sessao
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.shared.exceptions import DomainError
from infrastructure.config.settings import settings
from infrastructure.di import get_gerenciador_conexoes, get_provedor_token, get_relogio, get_repositorio_usuario, get_uow

SUBPROTOCOLO_TOKEN = "sgopi.bearer"

router = APIRouter(tags=["tempo-real"])


def token_do_subprotocolo(ws: WebSocket) -> str | None:
    protocolos = [p.strip() for p in ws.headers.get("sec-websocket-protocol", "").split(",") if p.strip()]
    if len(protocolos) == 2 and protocolos[0] == SUBPROTOCOLO_TOKEN:
        return protocolos[1]
    return None


def origem_permitida(ws: WebSocket) -> bool:
    origem = ws.headers.get("origin")
    return origem is None or origem in settings.cors_origins


@router.websocket("/v1/tempo-real")
async def tempo_real(
    ws: WebSocket,
    usuarios: RepositorioUsuario = Depends(get_repositorio_usuario),
    uow: UnidadeDeTrabalho = Depends(get_uow),
) -> None:
    if not origem_permitida(ws):
        await ws.close(code=CODIGO_POLITICA_VIOLADA, reason="origem não permitida")
        return
    relogio = get_relogio()
    try:
        ator, expira_em = extrair_sessao(token_do_subprotocolo(ws), ws, get_provedor_token(), relogio)  # type: ignore[arg-type]
        await exigir_usuario_ativo(ator, usuarios)
    except DomainError:
        await ws.close(code=CODIGO_POLITICA_VIOLADA, reason="token inválido")
        return
    finally:
        await uow.rollback()  # libera a conexão do pool: o socket vive horas e não usa mais o banco
    gerenciador = get_gerenciador_conexoes()
    await gerenciador.conectar(ws, Sessao(ator=ator, expira_em=expira_em), subprotocolo=SUBPROTOCOLO_TOKEN)
    try:
        while True:
            # canal é unidirecional (servidor → painel); mensagens do cliente servem como keep-alive
            await ws.receive_text()
            if await gerenciador.encerrar_se_expirada(ws, relogio.agora()):
                return
    except WebSocketDisconnect:
        pass
    finally:
        gerenciador.desconectar(ws)
