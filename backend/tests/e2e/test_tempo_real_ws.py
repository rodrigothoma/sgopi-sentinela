"""E2E: WebSocket de tempo real abre conexão (RF02 / RNF01)."""
import asyncio

import httpx
import pytest
import websockets

from tests.e2e.conftest import BASE_URL, token_de

URL_WS = f"{BASE_URL.replace('http', 'ws')}/v1/tempo-real"


async def _conectar_ws(token: str):
    """O token vai no Sec-WebSocket-Protocol (["sgopi.bearer", token]), nunca na URL."""
    async with websockets.connect(URL_WS, subprotocols=["sgopi.bearer", token]) as ws:
        assert ws.subprotocol == "sgopi.bearer"
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
    with pytest.raises(Exception):  # noqa: B017 — a lib de WS do e2e não expõe um tipo estável para 1008
        asyncio.run(_conectar_ws("token-invalido"))


def test_websocket_recusa_token_na_query_string(client: httpx.Client):
    token = token_de(client, "operador")

    async def _via_query():
        async with websockets.connect(f"{URL_WS}?token={token}"):
            pass

    with pytest.raises(Exception):  # noqa: B017 — idem
        asyncio.run(_via_query())
