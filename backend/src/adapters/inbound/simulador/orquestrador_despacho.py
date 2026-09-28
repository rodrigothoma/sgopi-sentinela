"""
Orquestrador de despacho/encerramento automáticos (Issues #62/#63 — RF02/RF18/RF19/RNF04).

*Driving adapter* opt-in: a cada ciclo observa o banco e chama os MESMOS casos de
uso do Operador humano (``DespacharViatura``/``EncerrarOcorrencia``). Nenhuma
alteração em domain/, application/, ports/, migrações ou na máquina de estados.

Regras implementadas:
- Só despacha ocorrência ``VALIDADA`` esperando além de ``janela_carencia_segundos``
  (medido por ``atualizada_em`` == instante da validação);
- A viatura ``DISPONIVEL`` mais próxima é escolhida pelo serviço de proximidade do
  domínio (Haversine + ``posicao_valida``) — nunca recalcula distância aqui (RNF04);
- Viatura com GPS vencido (> ``max_idade_segundos``) nunca é despachada (RNF04);
- Teto de despachos simultâneos (tamanho da frota da demo) e unicidade por viatura;
- Só encerra após a viatura chegar (``OPERANDO``) + ``tempo_atendimento_segundos``;
  instante da chegada é mantido em memória (``Viatura`` não tem ``chegou_em``);
- Ocorrência com apoio manual (múltiplas ordens ativas, Issue #64) nunca é
  encerrada automaticamente — o operador encerra quando quiser liberar todas;
- Carência evita disputa com o despacho manual do painel (sem 409/422 espúrios).

Ligado/desligado junto com a telemetria via ``/v1/simulador``; desligado por padrão
e nunca ativo em testes automatizados.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from uuid import UUID

from adapters.inbound.simulador.catalogo_demo import MARCA_SIMULADO
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_despachar_viatura import (
    DespacharInput,
    EncerrarInput,
    InterfaceDespacharViatura,
    InterfaceEncerrarOcorrencia,
)
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import (
    FiltroOcorrencias,
    RepositorioOcorrencia,
)
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.despacho.servico_proximidade import sugerir_viaturas_proximas
from domain.ocorrencia.status import StatusOcorrencia
from domain.viatura.entity import SituacaoViatura

log = logging.getLogger("sgopi.orquestrador_despacho")

# Teto de despachos simultâneos com a frota do seed (5 viaturas). A capacidade real
# também é limitada pelas viaturas DISPONIVEL do tick.
TETO_DESPACHOS_SIMULTANEOS = 5
LIMITE_ORDENS_ATIVAS = 500
LIMITE_OCORRENCIAS = 100
OBSERVACOES_DESPACHO = "Despacho automático (simulação)"

# Tipo do contexto entregue pela fábrica do composition root por ciclo de decisão.
Contexto = tuple[
    RepositorioViatura,
    RepositorioOcorrencia,
    RepositorioOrdemDespacho,
    InterfaceDespacharViatura,
    InterfaceEncerrarOcorrencia,
    Ator | None,
    Ator | None,
]


class OrquestradorDespacho:
    def __init__(
        self,
        fabrica_contexto: Callable[[], AbstractAsyncContextManager[Contexto]],
        relogio: Relogio,
        intervalo_segundos: float = 5.0,
        janela_carencia_segundos: int = 20,
        tempo_atendimento_segundos: int = 45,
        max_idade_segundos: int = 60,
        teto_despachos: int = TETO_DESPACHOS_SIMULTANEOS,
    ) -> None:
        if intervalo_segundos < 1.0:
            raise ValueError("intervalo do orquestrador deve ser >= 1s.")
        self._fabrica = fabrica_contexto
        self._relogio = relogio
        self.intervalo = intervalo_segundos
        self.janela_carencia = janela_carencia_segundos
        self.tempo_atendimento = tempo_atendimento_segundos
        self.max_idade = max_idade_segundos
        self.teto_despachos = teto_despachos
        self._tarefa: asyncio.Task | None = None
        self._parar_event = asyncio.Event()
        # Instante da chegada ao local por viatura (em memória, como o cache de rotas).
        self._chegadas: dict[UUID, datetime] = {}
        self.ticks = 0
        self.ocioso = 0
        self.despachados = 0
        self.encerrados = 0

    @property
    def ligado(self) -> bool:
        return self._tarefa is not None and not self._tarefa.done()

    def status(self) -> dict:
        return {
            "ligado": self.ligado,
            "intervalo_segundos": self.intervalo,
            "janela_carencia_segundos": self.janela_carencia,
            "tempo_atendimento_segundos": self.tempo_atendimento,
            "ticks": self.ticks,
            "ocioso": self.ocioso,
            "despachados": self.despachados,
            "encerrados": self.encerrados,
        }

    async def ligar(self) -> bool:
        """Liga o loop; sem 'simulador-operador'/'simulador-delegado', loga 'rode o seed' e não inicia."""
        if self.ligado:
            return True
        try:
            async with self._fabrica() as (_, _, _, _, _, ator_operador, ator_delegado):
                if ator_operador is None or ator_delegado is None:
                    log.warning("orquestrador: usuários 'simulador-operador'/'simulador-delegado' não encontrados — rode o seed; não iniciado")
                    return False
        except Exception:  # noqa: BLE001 — orquestrador nunca derruba o servidor
            log.exception("orquestrador: falha ao verificar atores; não iniciado")
            return False
        self._parar_event.clear()
        self._tarefa = asyncio.create_task(self._loop(), name="orquestrador-despacho")
        log.info("orquestrador ligado (%.0fs, carência %ds, atendimento %ds)", self.intervalo, self.janela_carencia, self.tempo_atendimento)
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
        log.info("orquestrador desligado após %d ticks (%d despachados, %d encerrados)", self.ticks, self.despachados, self.encerrados)

    async def _loop(self) -> None:
        while not self._parar_event.is_set():
            try:
                await self.tick()
            except Exception:  # noqa: BLE001 — orquestrador nunca derruba a API
                log.exception("tick do orquestrador falhou")
            try:
                await asyncio.wait_for(self._parar_event.wait(), timeout=self.intervalo)
                break
            except asyncio.TimeoutError:
                pass

    # ------------------------------------------------------------------ decisão

    def _desfecho(self, prefixo: str) -> str:
        return f"{MARCA_SIMULADO} Atendimento simulado concluído pela viatura {prefixo}."

    async def tick(self) -> None:
        """Um ciclo de decisão; nunca levanta para o chamador (log e segue)."""
        agora = self._relogio.agora()
        agiu = False
        try:
            async with self._fabrica() as contexto:
                viaturas, ocorrencias, ordens, despachar, encerrar = contexto[0], contexto[1], contexto[2], contexto[3], contexto[4]
                ator_operador, ator_delegado = contexto[5], contexto[6]
                if ator_operador is None or ator_delegado is None:
                    log.warning("orquestrador: atores do seed ausentes — rode o seed")
                    self.ticks += 1
                    self.ocioso += 1
                    return
                ativas = await ordens.listar(None, somente_ativas=True, limit=LIMITE_ORDENS_ATIVAS)
                if await self._processar_encerramentos(viaturas, encerrar, ator_delegado, ativas, agora):
                    agiu = True
                if await self._processar_despachos(viaturas, ocorrencias, despachar, ator_operador, ativas, agora):
                    agiu = True
        except Exception as exc:  # noqa: BLE001 — falha de leitura não derruba o tick
            log.warning("orquestrador: ciclo falhou, tentando no próximo: %s", exc)
        finally:
            self.ticks += 1
            if not agiu:
                self.ocioso += 1

    async def _processar_encerramentos(
        self,
        viaturas: RepositorioViatura,
        encerrar: InterfaceEncerrarOcorrencia,
        ator_delegado: Ator,
        ativas: list,
        agora: datetime,
    ) -> bool:
        agiu = False
        ids_ativos = {ordem.viatura_id for ordem in ativas}
        for viatura_id in list(self._chegadas):
            if viatura_id not in ids_ativos:
                self._chegadas.pop(viatura_id, None)  # ordem encerrada manualmente: limpa rastro
        ordens_por_ocorrencia: dict[UUID, int] = {}
        for ordem in ativas:
            ordens_por_ocorrencia[ordem.ocorrencia_id] = ordens_por_ocorrencia.get(ordem.ocorrencia_id, 0) + 1
        for ordem in ativas:
            if ordens_por_ocorrencia[ordem.ocorrencia_id] != 1:
                continue  # apoio manual (Issue #64): encerramento é decisão do operador
            viatura = await viaturas.buscar_por_id(ordem.viatura_id)
            if viatura is None or viatura.situacao != SituacaoViatura.OPERANDO:
                continue
            chegada = self._chegadas.get(ordem.viatura_id)
            if chegada is None:
                self._chegadas[ordem.viatura_id] = agora  # chegada observada neste ciclo
                continue
            if (agora - chegada).total_seconds() < self.tempo_atendimento:
                continue
            try:
                await encerrar.executar(
                    ator_delegado,
                    EncerrarInput(ocorrencia_id=ordem.ocorrencia_id, desfecho=self._desfecho(viatura.prefixo)),
                )
                self.encerrados += 1
                agiu = True
                log.info("orquestrador encerrou ordem %s (ocorrência %s, viatura %s)", ordem.numero, ordem.ocorrencia_id, viatura.prefixo)
            except Exception as exc:  # noqa: BLE001 — corrida com encerramento manual vira log
                log.warning("orquestrador: falha ao encerrar %s: %s", ordem.numero, exc)
            finally:
                self._chegadas.pop(ordem.viatura_id, None)
        return agiu

    async def _processar_despachos(
        self,
        viaturas: RepositorioViatura,
        ocorrencias: RepositorioOcorrencia,
        despachar: InterfaceDespacharViatura,
        ator_operador: Ator,
        ativas: list,
        agora: datetime,
    ) -> bool:
        capacidade = self.teto_despachos - len(ativas)
        if capacidade <= 0:
            return False
        empenhadas = {ordem.ocorrencia_id for ordem in ativas}
        candidatas = [
            o for o in await ocorrencias.listar(FiltroOcorrencias(status=(StatusOcorrencia.VALIDADA,), limit=LIMITE_OCORRENCIAS))
            if o.id not in empenhadas and (agora - o.atualizada_em).total_seconds() >= self.janela_carencia
        ][:capacidade]
        if not candidatas:
            return False
        frota = [v for v in await viaturas.listar((SituacaoViatura.DISPONIVEL,))]
        usadas: set[UUID] = set()
        agiu = False
        for o in candidatas:
            restantes = [v for v in frota if v.id not in usadas]
            sugeridas = sugerir_viaturas_proximas(o.coordenada, restantes, agora, self.max_idade, quantidade=1)
            if not sugeridas:
                if restantes:
                    log.info(
                        "orquestrador: %d viatura(s) DISPONIVEL sem GPS válido (RNF04) — despacho automático bloqueado para %s",
                        len(restantes),
                        o.numero_protocolo,
                    )
                continue
            viatura = sugeridas[0].viatura
            try:
                await despachar.executar(
                    ator_operador,
                    DespacharInput(ocorrencia_id=o.id, viatura_id=viatura.id, observacoes=OBSERVACOES_DESPACHO),
                )
                self.despachados += 1
                usadas.add(viatura.id)
                agiu = True
                log.info("orquestrador despachou %s para a ocorrência %s", viatura.prefixo, o.numero_protocolo)
            except Exception as exc:  # noqa: BLE001 — corrida com despacho manual vira log
                log.warning("orquestrador: falha ao despachar para %s: %s", o.numero_protocolo, exc)
        return agiu