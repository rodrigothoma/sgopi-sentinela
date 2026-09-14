"""
GerenciadorConexoesWebSocket (RF17): assina o PublicadorEventos e faz fan-out
para todos os painéis conectados. Conexões mortas são descartadas silenciosamente.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket

from domain.shared.eventos import EventoDominio

log = logging.getLogger("sgopi.ws")


def serializar(evento: EventoDominio) -> str:
    return json.dumps({"tipo": evento.tipo, "ocorrido_em": evento.ocorrido_em.isoformat(), "dados": evento.dados}, default=str)


class GerenciadorConexoes:
    def __init__(self) -> None:
        self._conexoes: set[WebSocket] = set()
        self.enviados = 0

    @property
    def total(self) -> int:
        return len(self._conexoes)

    async def conectar(self, ws: WebSocket) -> None:
        await ws.accept()
        self._conexoes.add(ws)
        log.info("painel conectado (%d ativos)", self.total)

    def desconectar(self, ws: WebSocket) -> None:
        self._conexoes.discard(ws)
        log.info("painel desconectado (%d ativos)", self.total)

    async def transmitir(self, evento: EventoDominio) -> None:
        if not self._conexoes:
            return
        mensagem = serializar(evento)
        resultados = await asyncio.gather(*(ws.send_text(mensagem) for ws in list(self._conexoes)), return_exceptions=True)
        for ws, r in zip(list(self._conexoes), resultados, strict=False):
            if isinstance(r, Exception):
                self.desconectar(ws)
        self.enviados += 1
