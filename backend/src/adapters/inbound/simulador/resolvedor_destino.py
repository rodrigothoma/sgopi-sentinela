"""Descoberta do destino do simulador (issue #54, RF02).

``ResolvedorDestino`` é definido dentro do módulo do simulador e implementado
sobre os repositórios já existentes — nenhuma porta é alterada. O estado é
lido do banco a cada tick (sobrevive a restart, sem mapa em memória).
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from domain.shared.geo import Coordenada

log = logging.getLogger("sgopi.simulador")


class ResolvedorDestino(ABC):
    @abstractmethod
    async def destinos(self, viatura_ids: list[UUID]) -> dict[UUID, Coordenada]:
        """Coordenada da ocorrência vinculada a cada viatura com ordem ativa."""
        ...


class ResolvedorDestinoRepositorios(ResolvedorDestino):
    """Lê ordens ativas e a coordenada da ocorrência vinculada.

    Acesso em lote: 1 ``listar`` de ordens ativas por tick + 1 busca de
    ocorrência por ordem ativa (limitada aos despachos simultâneos, sem
    consulta por viatura — sem N+1 por viatura). Falha de leitura vira
    "sem destino" (passeio aleatório) com log, sem derrubar o tick.
    """

    def __init__(self, ordens: RepositorioOrdemDespacho, ocorrencias: RepositorioOcorrencia) -> None:
        self._ordens = ordens
        self._ocorrencias = ocorrencias

    async def destinos(self, viatura_ids: list[UUID]) -> dict[UUID, Coordenada]:
        try:
            return await self._destinos(viatura_ids)
        except Exception as exc:  # noqa: BLE001 — telemetria simulada nunca derruba o tick
            log.warning("resolvedor de destino indisponível, sem destino neste tick: %s", exc)
            return {}

    async def _destinos(self, viatura_ids: list[UUID]) -> dict[UUID, Coordenada]:
        alvos = set(viatura_ids)
        ativas = await self._ordens.listar(None, somente_ativas=True, limit=max(len(alvos), 1))
        resultado: dict[UUID, Coordenada] = {}
        for ordem in ativas:
            if ordem.viatura_id not in alvos or ordem.viatura_id in resultado:
                continue
            ocorrencia = await self._ocorrencias.buscar_por_id(ordem.ocorrencia_id)
            if ocorrencia is not None:
                resultado[ordem.viatura_id] = ocorrencia.coordenada
        return resultado


class ResolvedorDestinoSessao(ResolvedorDestino):
    """Abre/fecha uma sessão de leitura por tick via a fábrica informada.

    A fábrica (mesma do ``di.montar_simulador``) rende os repositórios de
    ordens e ocorrências já ligados à sessão do tick. Falha ao abrir a
    sessão vira "sem destino" com log, sem derrubar o tick.
    """

    def __init__(
        self,
        fabrica: Callable[[], AbstractAsyncContextManager[tuple[RepositorioOrdemDespacho, RepositorioOcorrencia]]],
    ) -> None:
        self._fabrica = fabrica

    async def destinos(self, viatura_ids: list[UUID]) -> dict[UUID, Coordenada]:
        try:
            async with self._fabrica() as (ordens, ocorrencias):
                return await ResolvedorDestinoRepositorios(ordens, ocorrencias).destinos(viatura_ids)
        except Exception as exc:  # noqa: BLE001 — telemetria simulada nunca derruba o tick
            log.warning("sessão de destinos indisponível, sem destino neste tick: %s", exc)
            return {}
