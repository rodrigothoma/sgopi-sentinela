"""
GeradorOcorrencias (Issue #55, RF01) — *driving adapter*: chama a mesma porta
que o formulário usa (``InterfaceRegistrarOcorrenciaPolicial``).

Gera ocorrências fictícias ``AGUARDANDO_REVISAO`` marcadas com
``MARCA_SIMULADO`` para a Fila do Delegado (após refresh). Painel/heatmap só
refletem após validação manual — fora de escopo: WS da fila e filtro do heatmap.
Primeira geração ocorre após o primeiro intervalo. Erros nunca derrubam o loop.
"""
from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from adapters.inbound.simulador.catalogo_demo import (
    CENARIOS_DEMO,
    COMUNICANTES_DEMO,
    MARCA_SIMULADO,
)
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from application.ports.outbound.relogio import Relogio

log = logging.getLogger("sgopi.gerador_ocorrencias")


class GeradorOcorrencias:
    def __init__(
        self,
        fabrica_contexto: Callable[[], AbstractAsyncContextManager[tuple[Ator | None, InterfaceRegistrarOcorrenciaPolicial]]],
        relogio: Relogio,
        intervalo_segundos: float = 120.0,
        semente: int | None = None,
    ) -> None:
        if intervalo_segundos < 1.0:
            raise ValueError("intervalo do gerador deve ser >= 1s (Issue #55).")
        self._fabrica = fabrica_contexto
        self._relogio = relogio
        self.intervalo = intervalo_segundos
        self._rng = random.Random(semente)
        self._tarefa: asyncio.Task | None = None
        self._parar_event = asyncio.Event()
        self.ticks = 0
        self.geradas = 0

    @property
    def ligado(self) -> bool:
        return self._tarefa is not None and not self._tarefa.done()

    def status(self) -> dict:
        return {
            "ligado": self.ligado,
            "intervalo_segundos": self.intervalo,
            "ticks": self.ticks,
            "geradas": self.geradas,
        }

    async def ligar(self) -> bool:
        """Liga o loop; se simulador-demo não existir, loga 'rode o seed' e não inicia."""
        if self.ligado:
            return True
        try:
            async with self._fabrica() as (ator, _):
                if ator is None:
                    log.warning("gerador: usuário 'simulador-demo' não encontrado — rode o seed; gerador não iniciado")
                    return False
        except Exception:  # noqa: BLE001 — gerador nunca derruba o servidor
            log.exception("gerador: falha ao verificar ator; gerador não iniciado")
            return False
        self._parar_event.clear()
        self._tarefa = asyncio.create_task(self._loop(), name="gerador-ocorrencias")
        log.info("gerador de ocorrências ligado (intervalo %.0fs)", self.intervalo)
        return True

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
        log.info("gerador desligado após %d ticks (%d geradas)", self.ticks, self.geradas)

    async def _loop(self) -> None:
        # Primeira geração após o primeiro intervalo (ajuste 3).
        while not self._parar_event.is_set():
            try:
                await asyncio.wait_for(self._parar_event.wait(), timeout=self.intervalo)
                break
            except asyncio.TimeoutError:
                pass
            try:
                await self.tick()
            except Exception:  # noqa: BLE001 — gerador nunca derruba a API
                log.exception("tick do gerador falhou")

    def _sortear_input(self) -> RegistrarOcorrenciaInput:
        cenario = self._rng.choice(CENARIOS_DEMO)
        comunicante = self._rng.choice(COMUNICANTES_DEMO)
        agora = self._relogio.agora()
        return RegistrarOcorrenciaInput(
            natureza=cenario.natureza,
            descricao=f"{MARCA_SIMULADO} {cenario.descricao_base}",
            localizacao=cenario.localizacao,
            latitude=cenario.coordenada.latitude,
            longitude=cenario.coordenada.longitude,
            data_hora_fato=agora,
            tipificacoes=(TipificacaoInputDTO(artigo=cenario.artigo, descricao=cenario.artigo_descricao),),
            envolvidos=(
                EnvolvidoInputDTO(nome=comunicante.nome, tipo="COMUNICANTE", documento=comunicante.documento),
            ),
        )

    async def tick(self) -> int:
        """Um ciclo de geração; devolve 1 se gerou, 0 caso contrário."""
        try:
            async with self._fabrica() as (ator, registrar):
                if ator is None:
                    log.warning("gerador: usuário 'simulador-demo' não encontrado — rode o seed")
                    return 0
                await registrar.executar(ator, self._sortear_input())
                self.geradas += 1
                return 1
        except Exception:  # noqa: BLE001 — erro de registro logado sem derrubar o loop
            log.exception("gerador: falha ao registrar ocorrência fictícia")
            return 0
        finally:
            self.ticks += 1
