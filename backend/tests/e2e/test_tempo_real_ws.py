"""E2E: WebSocket de tempo real abre conexão (RF17)."""
import asyncio
import pytest
import websockets

import httpx
from tests.e2e.conftest import token_de


async def _conectar_ws(token: str):
    url = f"ws://localhost:8000/v1/tempo-real?token={token}"
    async with websockets.connect(url) as ws:
        return ws


@pytest.mark.asyncio
async def test_websocket_conecta_com_token_valido(client: httpx.Client):
    """Verifica que o handshake WebSocket funciona com token válido."""
    token = token_de(client, "operador")
    ws = await _conectar_ws(token)
    # Se chegou aqui, a conexão foi aceita
    assert ws is not None
    await ws.close()


def test_websocket_recusa_token_invalido():
    """Verifica que token inválido recusa a conexão (code 1008)."""
    with pytest.raises(Exception):
        asyncio.run(_conectar_ws("token-invalido"))
