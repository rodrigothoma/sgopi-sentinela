"""
WS /v1/tempo-real (RF02 / RNF01).

Navegadores não enviam headers customizados no handshake; o token vai no cabeçalho
``Sec-WebSocket-Protocol`` como ``["sgopi.bearer", <jwt>]`` — nunca na URL, que
acaba em logs de acesso, proxies e histórico. O servidor responde só ``sgopi.bearer``.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from adapters.inbound.http.deps import extrair_ator
from domain.shared.exceptions import DomainError
from infrastructure.di import get_gerenciador_conexoes, get_provedor_token, get_relogio

SUBPROTOCOLO_TOKEN = "sgopi.bearer"

router = APIRouter(tags=["tempo-real"])


def token_do_subprotocolo(ws: WebSocket) -> str | None:
    protocolos = [p.strip() for p in ws.headers.get("sec-websocket-protocol", "").split(",") if p.strip()]
    if len(protocolos) == 2 and protocolos[0] == SUBPROTOCOLO_TOKEN:
        return protocolos[1]
    return None


@router.websocket("/v1/tempo-real")
async def tempo_real(ws: WebSocket) -> None:
    try:
        extrair_ator(token_do_subprotocolo(ws), ws, get_provedor_token(), get_relogio())  # type: ignore[arg-type]
    except DomainError:
        await ws.close(code=1008, reason="token inválido")
        return
    gerenciador = get_gerenciador_conexoes()
    await gerenciador.conectar(ws, subprotocolo=SUBPROTOCOLO_TOKEN)
    try:
        while True:
            # canal é unidirecional (servidor → painel); mensagens do cliente servem como keep-alive
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        gerenciador.desconectar(ws)
