"""
GerenciadorConexoesWebSocket (RF02 / RNF01): assina o PublicadorEventos e faz fan-out
para os painéis conectados, respeitando a audiência de cada evento (``audiencia.py``).

Cada conexão guarda o ``Ator`` e a expiração do token: sessão vencida é fechada com 1008 em
vez de continuar recebendo eventos. Conexões mortas ou lentas são descartadas.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

from fastapi import WebSocket

from adapters.inbound.websocket.audiencia import pode_receber
from application.ports.inbound.ator import Ator
from application.ports.outbound.relogio import Relogio
from domain.shared.eventos import EventoDominio

log = logging.getLogger("sgopi.ws")

CODIGO_POLITICA_VIOLADA = 1008
TIMEOUT_ENVIO_SEGUNDOS = 5.0


def serializar(evento: EventoDominio) -> str:
    return json.dumps({"tipo": evento.tipo, "ocorrido_em": evento.ocorrido_em.isoformat(), "dados": evento.dados}, default=str)


@dataclass(frozen=True)
class Sessao:
    ator: Ator
    expira_em: datetime


class GerenciadorConexoes:
    def __init__(self, relogio: Relogio) -> None:
        self._relogio = relogio
        self._conexoes: dict[WebSocket, Sessao] = {}
        self.enviados = 0

    @property
    def total(self) -> int:
        return len(self._conexoes)

    async def conectar(self, ws: WebSocket, sessao: Sessao, subprotocolo: str | None = None) -> None:
        await ws.accept(subprotocol=subprotocolo)
        self._conexoes[ws] = sessao
        log.info("painel conectado (%d ativos)", self.total)

    def desconectar(self, ws: WebSocket) -> None:
        if self._conexoes.pop(ws, None) is not None:
            log.info("painel desconectado (%d ativos)", self.total)

    async def encerrar_se_expirada(self, ws: WebSocket, agora: datetime) -> bool:
        """Fecha a conexão cujo token venceu; devolve True se fechou."""
        sessao = self._conexoes.get(ws)
        if sessao is None or sessao.expira_em > agora:
            return False
        self.desconectar(ws)
        try:
            await ws.close(code=CODIGO_POLITICA_VIOLADA, reason="sessão expirada")
        except Exception:
            pass
        return True

    async def transmitir(self, evento: EventoDominio) -> None:
        if not self._conexoes:
            return
        agora = self._relogio.agora()
        alvos = [ws for ws, s in list(self._conexoes.items()) if pode_receber(evento, s.ator)]
        expirados = [ws for ws in alvos if self._conexoes[ws].expira_em <= agora]
        for ws in expirados:
            await self.encerrar_se_expirada(ws, agora)
        alvos = [ws for ws in alvos if ws not in expirados]
        if not alvos:
            return
        mensagem = serializar(evento)
        resultados = await asyncio.gather(
            *(asyncio.wait_for(ws.send_text(mensagem), TIMEOUT_ENVIO_SEGUNDOS) for ws in alvos), return_exceptions=True
        )
        for ws, r in zip(alvos, resultados, strict=True):
            if isinstance(r, BaseException):
                self.desconectar(ws)
        self.enviados += 1
