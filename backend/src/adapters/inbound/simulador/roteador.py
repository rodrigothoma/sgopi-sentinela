"""Roteamento do simulador com destino (issue #54, RF02).

A rota é detalhe de telemetria simulada (driving adapter): ``Roteador`` devolve
a lista de pontos pelas ruas entre duas coordenadas. ``RoteadorLinhaReta`` é o
fallback sem rede; ``RoteadorOSRM`` consulta um serviço OSRM via stdlib
(``urllib``) com timeout curto — qualquer falha vira ``ErroRoteamento`` e o
chamador cai para a linha reta, sem travar.

A chamada é síncrona de propósito: o tick (async) a executa via
``asyncio.to_thread`` para não bloquear o event loop.
"""
from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Callable

from domain.shared.geo import Coordenada


class ErroRoteamento(Exception):
    """Serviço de rotas indisponível ou resposta inválida (usa-se linha reta)."""


class Roteador(ABC):
    @abstractmethod
    def rota(self, origem: Coordenada, destino: Coordenada) -> list[Coordenada]:
        """Pontos pelas ruas de ``origem`` até ``destino`` (vazia = sem rota)."""
        ...


class RoteadorLinhaReta(Roteador):
    """Fallback sem rede: sempre 2 pontos (origem, destino)."""

    def rota(self, origem: Coordenada, destino: Coordenada) -> list[Coordenada]:
        return [origem, destino]


class RoteadorOSRM(Roteador):
    """Consulta ``{base}/route/v1/driving/...?geometries=geojson`` (OSRM)."""

    def __init__(
        self,
        base_url: str,
        timeout_segundos: float = 2.0,
        buscar: Callable[[str], dict] | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout_segundos
        self._buscar = buscar or self._buscar_via_http

    def rota(self, origem: Coordenada, destino: Coordenada) -> list[Coordenada]:
        url = (
            f"{self._base}/route/v1/driving/"
            f"{origem.longitude},{origem.latitude};{destino.longitude},{destino.latitude}"
            "?overview=full&geometries=geojson"
        )
        try:
            dados = self._buscar(url)
        except ErroRoteamento:
            raise
        except Exception as exc:
            raise ErroRoteamento(f"Falha ao consultar o roteador: {exc}") from exc
        return self._parse(dados)

    def _buscar_via_http(self, url: str) -> dict:
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except Exception as exc:
            raise ErroRoteamento(f"Falha ao consultar o roteador: {exc}") from exc

    @staticmethod
    def _parse(dados: object) -> list[Coordenada]:
        """Converte pares [lon, lat] do GeoJSON em ``Coordenada`` (lat, lon)."""
        try:
            assert isinstance(dados, dict)
            assert dados.get("code") == "Ok"
            rotas = dados["routes"]
            assert isinstance(rotas, list) and rotas
            pares = rotas[0]["geometry"]["coordinates"]
            assert isinstance(pares, list)
            return [Coordenada(latitude=float(lon_lat[1]), longitude=float(lon_lat[0])) for lon_lat in pares]
        except (AssertionError, KeyError, TypeError, ValueError) as exc:
            raise ErroRoteamento(f"Resposta de rota inválida: {exc}") from exc
