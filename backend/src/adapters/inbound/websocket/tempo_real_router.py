"""WS /v1/tempo-real (RF17): token no query string (navegadores não enviam headers no handshake)."""
from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from adapters.inbound.http.deps import extrair_ator
from domain.shared.exceptions import DomainError
from infrastructure.di import get_gerenciador_conexoes, get_provedor_token, get_relogio

router = APIRouter(tags=["tempo-real"])


@router.websocket("/v1/tempo-real")
async def tempo_real(ws: WebSocket, token: str | None = Query(default=None)) -> None:
    try:
        extrair_ator(token, ws, get_provedor_token(), get_relogio())  # type: ignore[arg-type]
    except DomainError:
        await ws.close(code=1008, reason="token inválido")
        return
    gerenciador = get_gerenciador_conexoes()
    await gerenciador.conectar(ws)
    try:
        while True:
            # canal é unidirecional (servidor → painel); mensagens do cliente servem como keep-alive
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        gerenciador.desconectar(ws)
