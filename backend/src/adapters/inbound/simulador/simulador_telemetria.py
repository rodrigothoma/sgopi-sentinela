"""
SimuladorTelemetria (RF16) — *driving adapter*: chama a mesma porta que um GPS
real chamaria (``InterfaceRegistrarPosicaoViatura``). Ligado/desligado pelo painel.

A cada tick:
- DISPONIVEL patrulha aleatoriamente dentro de um raio (viaturas sem posição nascem
  em torno de um centro configurável);
- EM_DESLOCAMENTO segue em linha reta, à velocidade configurada, até a ocorrência da
  sua ordem ativa — a chegada (→ OPERANDO) é detectada pelo caso de uso de posição;
- OPERANDO permanece no local, reemitindo a posição para manter o sinal GPS válido.
"""
from __future__ import annotations

import asyncio
import logging
import math
import random
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

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

# Resolve o destino de uma viatura despachada (coordenada da ocorrência da ordem ativa).
ResolvedorDestino = Callable[[UUID], Awaitable[Coordenada | None]]
# O contexto entrega (repositório, caso de uso de posição) e, opcionalmente, o resolvedor de destino.
Contexto = tuple[RepositorioViatura, InterfaceRegistrarPosicaoViatura] | tuple[RepositorioViatura, InterfaceRegistrarPosicaoViatura, ResolvedorDestino]


class SimuladorTelemetria:
    def __init__(
        self,
        fabrica_contexto: Callable[[], AbstractAsyncContextManager[Contexto]],
        relogio: Relogio,
        intervalo_segundos: float = 1.0,
        raio_metros: float = 150.0,
        centro: Coordenada = CENTRO_PADRAO,
        semente: int | None = None,
        velocidade_kmh: float = 120.0,
    ) -> None:
        self._fabrica = fabrica_contexto
        self._relogio = relogio
        self.intervalo = intervalo_segundos
        self.raio = raio_metros
        self.centro = centro
        self.velocidade_kmh = velocidade_kmh
        self._rng = random.Random(semente)
        self._tarefa: asyncio.Task | None = None
        self.ticks = 0
        self.posicoes_emitidas = 0
        self._parar_event = asyncio.Event()

    @property
    def ligado(self) -> bool:
        return self._tarefa is not None and not self._tarefa.done()

    def status(self) -> dict:
        return {
            "ligado": self.ligado, "intervalo_segundos": self.intervalo, "raio_metros": self.raio, "velocidade_kmh": self.velocidade_kmh,
            "ticks": self.ticks, "posicoes_emitidas": self.posicoes_emitidas,
        }

    def ligar(self) -> None:
        if self.ligado:
            return
        self._parar_event.clear()
        self._tarefa = asyncio.create_task(self._loop(), name="simulador-telemetria")
        log.info("simulador ligado (%.1fs, raio %.0fm)", self.intervalo, self.raio)

    async def desligar(self) -> None:
        if self._tarefa is None:
            return
        self._parar_event.set()
        if not self._tarefa.done():
            try:
                await asyncio.wait_for(asyncio.shield(self._tarefa), timeout=2.0)
            except asyncio.TimeoutError:
                self._tarefa.cancel()
                try:
                    await self._tarefa
                except asyncio.CancelledError:
                    pass
        self._tarefa = None
        log.info("simulador desligado após %d ticks", self.ticks)


    async def _loop(self) -> None:
        while not self._parar_event.is_set():
            try:
                await self.tick()
            except Exception:  # noqa: BLE001 — o simulador nunca derruba a API
                log.exception("tick do simulador falhou")
            try:
                await asyncio.wait_for(self._parar_event.wait(), timeout=self.intervalo)
                break
            except asyncio.TimeoutError:
                pass


    async def tick(self) -> int:
        """Um ciclo de emissão; devolve quantas posições foram aceitas."""
        agora = self._relogio.agora()
        aceitas = 0
        async with self._fabrica() as contexto:
            repositorio, registrar = contexto[0], contexto[1]
            resolver_destino: ResolvedorDestino | None = contexto[2] if len(contexto) > 2 else None
            viaturas = await repositorio.listar((SituacaoViatura.DISPONIVEL, SituacaoViatura.EM_DESLOCAMENTO, SituacaoViatura.OPERANDO))
            for v in viaturas:
                destino = None
                if v.situacao == SituacaoViatura.EM_DESLOCAMENTO and resolver_destino is not None:
                    destino = await resolver_destino(v.id)
                proxima = self._proxima_posicao(v, destino)
                try:
                    await registrar.executar(RegistrarPosicaoInput(viatura_id=v.id, latitude=proxima.latitude, longitude=proxima.longitude, registrada_em=agora, origem="simulador"))
                    aceitas += 1
                except DomainError as exc:
                    log.warning("posição simulada rejeitada para %s: %s", v.prefixo, exc)
        self.ticks += 1
        self.posicoes_emitidas += aceitas
        return aceitas

    @property
    def passo_deslocamento_metros(self) -> float:
        """Quanto uma viatura despachada avança por tick (velocidade × intervalo)."""
        return self.velocidade_kmh * 1000 / 3600 * self.intervalo

    def _proxima_posicao(self, v: Viatura, destino: Coordenada | None) -> Coordenada:
        origem = v.ultima_posicao.coordenada if v.ultima_posicao else self._ponto_inicial()
        if v.situacao == SituacaoViatura.OPERANDO:
            return origem  # no local do atendimento: só mantém o sinal
        if v.situacao == SituacaoViatura.EM_DESLOCAMENTO and destino is not None:
            return self._em_direcao_a(origem, destino)
        return self._patrulha(origem)

    def _patrulha(self, origem: Coordenada) -> Coordenada:
        angulo = self._rng.uniform(0, 2 * math.pi)
        passo = self._rng.uniform(0, self.raio)
        return self._deslocar(origem, passo, angulo)

    def _em_direcao_a(self, origem: Coordenada, destino: Coordenada) -> Coordenada:
        """Avança ``passo_deslocamento_metros`` rumo ao destino; no último trecho para exatamente nele."""
        restante = origem.distancia_km(destino) * 1000
        if restante <= self.passo_deslocamento_metros:
            return destino
        dlat = destino.latitude - origem.latitude
        dlon = (destino.longitude - origem.longitude) * math.cos(math.radians(origem.latitude))
        angulo = math.atan2(dlon, dlat)  # 0 = norte, π/2 = leste — mesma convenção de _deslocar
        return self._deslocar(origem, self.passo_deslocamento_metros, angulo)

    @staticmethod
    def _deslocar(origem: Coordenada, metros: float, angulo: float) -> Coordenada:
        dlat = (metros * math.cos(angulo)) / METROS_POR_GRAU_LAT
        dlon = (metros * math.sin(angulo)) / (METROS_POR_GRAU_LAT * max(math.cos(math.radians(origem.latitude)), 1e-6))
        return Coordenada(round(origem.latitude + dlat, 6), round(origem.longitude + dlon, 6))

    def _ponto_inicial(self) -> Coordenada:
        raio_inicial = self.raio * 20  # espalha a frota num raio ~3 km
        angulo = self._rng.uniform(0, 2 * math.pi)
        passo = self._rng.uniform(raio_inicial * 0.2, raio_inicial)
        dlat = (passo * math.cos(angulo)) / METROS_POR_GRAU_LAT
        dlon = (passo * math.sin(angulo)) / (METROS_POR_GRAU_LAT * math.cos(math.radians(self.centro.latitude)))
        return Coordenada(round(self.centro.latitude + dlat, 6), round(self.centro.longitude + dlon, 6))
