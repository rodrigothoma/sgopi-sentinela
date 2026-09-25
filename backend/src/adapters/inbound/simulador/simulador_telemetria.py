"""
SimuladorTelemetria (RF16) — *driving adapter*: chama a mesma porta que um GPS
real chamaria (``InterfaceRegistrarPosicaoViatura``). Ligado/desligado pelo painel.

A cada tick move todas as viaturas não-INDISPONIVEL; viaturas sem posição nascem
em torno de um centro configurável. Viaturas despachadas (``EM_DESLOCAMENTO``
com ordem ativa, issue #54) navegam pela rota até a ocorrência em vez do
passeio aleatório; ``OPERANDO`` com ordem ativa aguarda no local com jitter.
"""
from __future__ import annotations

import asyncio
import logging
import math
import random
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from adapters.inbound.simulador.navegacao import avancar_na_rota
from adapters.inbound.simulador.resolvedor_destino import ResolvedorDestino
from adapters.inbound.simulador.roteador import Roteador, RoteadorLinhaReta
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
# Falha no serviço de rotas: usa linha reta sem retentar a cada tick.
INTERVALO_RETENTATIVA_ROTEADOR_SEGUNDOS = 30.0


@dataclass
class _RotaEmCache:
    destino: Coordenada
    rota: list[Coordenada] = field(default_factory=list)
    indice: int = 0
    chegou: bool = False


class SimuladorTelemetria:
    def __init__(
        self,
        fabrica_contexto: Callable[[], AbstractAsyncContextManager[tuple[RepositorioViatura, InterfaceRegistrarPosicaoViatura]]],
        relogio: Relogio,
        intervalo_segundos: float = 1.0,
        raio_metros: float = 150.0,
        centro: Coordenada = CENTRO_PADRAO,
        semente: int | None = None,
        resolvedor: ResolvedorDestino | None = None,
        roteador: Roteador | None = None,
        passo_destino_metros: float = 300.0,
        raio_chegada_metros: float = 50.0,
        jitter_chegada_metros: float = 5.0,
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
        self._parar_event = asyncio.Event()
        self._resolvedor = resolvedor
        self._roteador = roteador or RoteadorLinhaReta()
        self.passo_destino = passo_destino_metros
        self.raio_chegada = raio_chegada_metros
        self.jitter_chegada = jitter_chegada_metros
        self._rotas: dict[UUID, _RotaEmCache] = {}
        self._roteador_falhou_em: datetime | None = None

    @property
    def ligado(self) -> bool:
        return self._tarefa is not None and not self._tarefa.done()

    def status(self) -> dict:
        return {
            "ligado": self.ligado, "intervalo_segundos": self.intervalo, "raio_metros": self.raio,
            "ticks": self.ticks, "posicoes_emitidas": self.posicoes_emitidas,
            "passo_destino_metros": self.passo_destino, "raio_chegada_metros": self.raio_chegada,
            "jitter_chegada_metros": self.jitter_chegada,
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
        async with self._fabrica() as (repositorio, registrar):
            viaturas = await repositorio.listar((SituacaoViatura.DISPONIVEL, SituacaoViatura.EM_DESLOCAMENTO, SituacaoViatura.OPERANDO))
            destinos = await self._resolvedor.destinos([v.id for v in viaturas]) if self._resolvedor else {}
            em_backoff = self._roteador_falhou_em is not None and (
                agora - self._roteador_falhou_em
            ).total_seconds() < INTERVALO_RETENTATIVA_ROTEADOR_SEGUNDOS
            for v in viaturas:
                destino = await self._proxima_posicao_navegada(v, destinos.get(v.id), agora, em_backoff)
                if destino is None:
                    destino = self._proxima_posicao(v)
                try:
                    await registrar.executar(RegistrarPosicaoInput(viatura_id=v.id, latitude=destino.latitude, longitude=destino.longitude, registrada_em=agora, origem="simulador"))
                    aceitas += 1
                except DomainError as exc:
                    log.warning("posição simulada rejeitada para %s: %s", v.prefixo, exc)
        self.ticks += 1
        self.posicoes_emitidas += aceitas
        return aceitas

    async def _obter_rota(self, origem: Coordenada, destino: Coordenada, agora: datetime, em_backoff: bool) -> list[Coordenada]:
        """Rota pelas ruas com fallback em linha reta (nunca trava o tick).

        O backoff é global do roteador (não por viatura) e vale para ticks
        futuros: dentro do mesmo tick cada viatura sem cache tenta uma vez.
        """
        if em_backoff:
            return [origem, destino]
        try:
            rota = await asyncio.to_thread(self._roteador.rota, origem, destino)
        except Exception as exc:  # noqa: BLE001 — serviço de rotas é externo e opcional
            log.warning("roteador indisponível, usando linha reta: %s", exc)
            self._roteador_falhou_em = agora
            return [origem, destino]
        if len(rota) < 2:
            log.warning("roteador devolveu rota vazia, usando linha reta")
            return [origem, destino]
        return rota

    async def _proxima_posicao_navegada(
        self, v: Viatura, destino: Coordenada | None, agora: datetime, em_backoff: bool
    ) -> Coordenada | None:
        """Posição seguinte pela rota (ou jitter no local); None = passeio aleatório.

        ``OPERANDO`` com ordem ativa fica parada onde chegou navegando (jitter
        em torno do último ponto da rota) ou, sem histórico de navegação, onde
        está (jitter na posição atual) — nunca teleporta para o destino.
        """
        if destino is None:
            self._rotas.pop(v.id, None)  # perdeu o destino: descarta a rota em cache
            return None
        if v.situacao == SituacaoViatura.DISPONIVEL:
            return None
        origem = v.ultima_posicao.coordenada if v.ultima_posicao else self._ponto_inicial()
        entrada = self._rotas.get(v.id)
        if entrada is None or entrada.destino != destino:
            rota = await self._obter_rota(origem, destino, agora, em_backoff)
            entrada = _RotaEmCache(destino=destino, rota=rota, indice=0)
            self._rotas[v.id] = entrada
        centro_chegada = entrada.rota[-1]  # último ponto: onde a viatura realmente chegou
        if v.situacao == SituacaoViatura.OPERANDO:
            if entrada.chegou:
                return self._ponto_aleatorio_em_torno(centro_chegada, self.jitter_chegada)
            return self._ponto_aleatorio_em_torno(origem, self.jitter_chegada)  # sem teleporte
        resultado = avancar_na_rota(origem, destino, entrada.rota, entrada.indice, self.passo_destino, self.raio_chegada)
        entrada.indice = resultado.indice_rota
        entrada.chegou = resultado.chegou
        if resultado.chegou:
            return self._ponto_aleatorio_em_torno(centro_chegada, self.jitter_chegada)
        return resultado.nova_posicao

    def _proxima_posicao(self, v: Viatura) -> Coordenada:
        origem = v.ultima_posicao.coordenada if v.ultima_posicao else self._ponto_inicial()
        return self._ponto_aleatorio_em_torno(origem, self.raio)

    def _ponto_aleatorio_em_torno(self, centro: Coordenada, raio_metros: float) -> Coordenada:
        angulo = self._rng.uniform(0, 2 * math.pi)
        passo = self._rng.uniform(0, raio_metros)
        dlat = (passo * math.cos(angulo)) / METROS_POR_GRAU_LAT
        dlon = (passo * math.sin(angulo)) / (METROS_POR_GRAU_LAT * max(math.cos(math.radians(centro.latitude)), 1e-6))
        return Coordenada(round(centro.latitude + dlat, 6), round(centro.longitude + dlon, 6))

    def _ponto_inicial(self) -> Coordenada:
        raio_inicial = self.raio * 20  # espalha a frota num raio ~3 km
        angulo = self._rng.uniform(0, 2 * math.pi)
        passo = self._rng.uniform(raio_inicial * 0.2, raio_inicial)
        dlat = (passo * math.cos(angulo)) / METROS_POR_GRAU_LAT
        dlon = (passo * math.sin(angulo)) / (METROS_POR_GRAU_LAT * math.cos(math.radians(self.centro.latitude)))
        return Coordenada(round(self.centro.latitude + dlat, 6), round(self.centro.longitude + dlon, 6))
