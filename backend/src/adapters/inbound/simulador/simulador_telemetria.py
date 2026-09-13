"""
SimuladorTelemetria (RF16) — *driving adapter*: chama a mesma porta que um GPS
real chamaria (``InterfaceRegistrarPosicaoViatura``). Ligado/desligado pelo painel.

A cada tick move todas as viaturas não-INDISPONIVEL aleatoriamente dentro de um raio;
viaturas sem posição nascem em torno de um centro configurável.
"""
from __future__ import annotations

import asyncio
import logging
import math
import random
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime

from application.ports.inbound.interface_gerir_viaturas import InterfaceRegistrarPosicaoViatura, RegistrarPosicaoInput
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.shared.exceptions import DomainError
from domain.shared.geo import Coordenada
from domain.viatura.entity import SituacaoViatura, Viatura

log = logging.getLogger("sgopi.simulador")

# Alegrete/RS — sede do curso (dados fictícios, RNF10)
CENTRO_PADRAO = Coordenada(-29.7833, -55.7919)
METROS_POR_GRAU_LAT = 111_320.0


class SimuladorTelemetria:
    def __init__(
        self,
        fabrica_contexto: Callable[[], AbstractAsyncContextManager[tuple[RepositorioViatura, InterfaceRegistrarPosicaoViatura]]],
        relogio: Relogio,
        intervalo_segundos: float = 1.0,
        raio_metros: float = 150.0,
        centro: Coordenada = CENTRO_PADRAO,
        semente: int | None = None,
    ) -> None:
        self._fabrica = fabrica_contexto
        self._relogio = relogio
        self.intervalo = intervalo_segundos
        self.raio = raio_metros
        self.centro = centro
        self._rng = random.Random(semente)
        self._tarefa: asyncio.Task | None = None
        self.ticks = 0
        self.posicoes_emitidas = 0

    @property
    def ligado(self) -> bool:
        return self._tarefa is not None and not self._tarefa.done()

    def status(self) -> dict:
        return {"ligado": self.ligado, "intervalo_segundos": self.intervalo, "raio_metros": self.raio, "ticks": self.ticks, "posicoes_emitidas": self.posicoes_emitidas}

    def ligar(self) -> None:
        if self.ligado:
            return
        self._tarefa = asyncio.create_task(self._loop(), name="simulador-telemetria")
        log.info("simulador ligado (%.1fs, raio %.0fm)", self.intervalo, self.raio)

    async def desligar(self) -> None:
        if self._tarefa is None:
            return
        self._tarefa.cancel()
        try:
            await self._tarefa
        except asyncio.CancelledError:
            pass
        self._tarefa = None
        log.info("simulador desligado após %d ticks", self.ticks)

    async def _loop(self) -> None:
        while True:
            try:
                await self.tick()
            except Exception:  # noqa: BLE001 — o simulador nunca derruba a API
                log.exception("tick do simulador falhou")
            await asyncio.sleep(self.intervalo)

    async def tick(self) -> int:
        """Um ciclo de emissão; devolve quantas posições foram aceitas."""
        agora = self._relogio.agora()
        aceitas = 0
        async with self._fabrica() as (repositorio, registrar):
            viaturas = await repositorio.listar((SituacaoViatura.DISPONIVEL, SituacaoViatura.EM_DESLOCAMENTO, SituacaoViatura.OPERANDO))
            for v in viaturas:
                destino = self._proxima_posicao(v)
                try:
                    await registrar.executar(RegistrarPosicaoInput(viatura_id=v.id, latitude=destino.latitude, longitude=destino.longitude, registrada_em=agora, origem="simulador"))
                    aceitas += 1
                except DomainError as exc:
                    log.warning("posição simulada rejeitada para %s: %s", v.prefixo, exc)
        self.ticks += 1
        self.posicoes_emitidas += aceitas
        return aceitas

    def _proxima_posicao(self, v: Viatura) -> Coordenada:
        origem = v.ultima_posicao.coordenada if v.ultima_posicao else self._ponto_inicial()
        angulo = self._rng.uniform(0, 2 * math.pi)
        passo = self._rng.uniform(0, self.raio)
        dlat = (passo * math.cos(angulo)) / METROS_POR_GRAU_LAT
        dlon = (passo * math.sin(angulo)) / (METROS_POR_GRAU_LAT * max(math.cos(math.radians(origem.latitude)), 1e-6))
        return Coordenada(round(origem.latitude + dlat, 6), round(origem.longitude + dlon, 6))

    def _ponto_inicial(self) -> Coordenada:
        raio_inicial = self.raio * 20  # espalha a frota num raio ~3 km
        angulo = self._rng.uniform(0, 2 * math.pi)
        passo = self._rng.uniform(raio_inicial * 0.2, raio_inicial)
        dlat = (passo * math.cos(angulo)) / METROS_POR_GRAU_LAT
        dlon = (passo * math.sin(angulo)) / (METROS_POR_GRAU_LAT * math.cos(math.radians(self.centro.latitude)))
        return Coordenada(round(self.centro.latitude + dlat, 6), round(self.centro.longitude + dlon, 6))
