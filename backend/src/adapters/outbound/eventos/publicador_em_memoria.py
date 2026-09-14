"""
Adapter de saída: PublicadorEventosEmMemoria (DEC-06).

Fan-out em processo para assinantes assíncronos (o gerenciador de conexões
WebSocket assina aqui). Um broker real é outro adapter na mesma porta.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from application.ports.outbound.publicador_eventos import PublicadorEventos
from domain.shared.eventos import EventoDominio

Assinante = Callable[[EventoDominio], Awaitable[None]]
log = logging.getLogger(__name__)


class PublicadorEventosEmMemoria(PublicadorEventos):
    def __init__(self) -> None:
        self._assinantes: list[Assinante] = []

    def assinar(self, assinante: Assinante) -> None:
        self._assinantes.append(assinante)

    def cancelar(self, assinante: Assinante) -> None:
        self._assinantes = [a for a in self._assinantes if a is not assinante]

    async def publicar(self, evento: EventoDominio) -> None:
        if not self._assinantes:
            return
        resultados = await asyncio.gather(*(a(evento) for a in self._assinantes), return_exceptions=True)
        for r in resultados:
            if isinstance(r, Exception):
                log.warning("assinante de eventos falhou: %s", r, extra={"evento": evento.tipo})
