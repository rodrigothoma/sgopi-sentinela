"""
LimitadorTentativasEmMemoria — implementação da porta LimitadorTentativas (RNF02).

Janela deslizante por chave, mantida no processo: adequada a uma instância única da API
(MVP). Com várias réplicas, trocar por uma implementação compartilhada (p.ex. Redis)
sem alterar os casos de uso.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

from application.ports.outbound.limitador_tentativas import LimitadorTentativas


class LimitadorTentativasEmMemoria(LimitadorTentativas):
    def __init__(self, max_tentativas: int, janela_segundos: float, bloqueio_segundos: float) -> None:
        if max_tentativas < 1 or janela_segundos <= 0 or bloqueio_segundos <= 0:
            raise ValueError("Política de limite inválida: máximo ≥ 1 e janela/bloqueio > 0.")
        self._max = max_tentativas
        self._janela = timedelta(seconds=janela_segundos)
        self._bloqueio = timedelta(seconds=bloqueio_segundos)
        self._tentativas: dict[str, deque[datetime]] = {}
        self._bloqueadas: dict[str, datetime] = {}

    def bloqueado_ate(self, chave: str, agora: datetime) -> datetime | None:
        fim = self._bloqueadas.get(chave)
        if fim is None:
            return None
        if fim <= agora:
            del self._bloqueadas[chave]
            return None
        return fim

    def registrar(self, chave: str, agora: datetime) -> None:
        tentativas = self._tentativas.setdefault(chave, deque())
        while tentativas and agora - tentativas[0] >= self._janela:
            tentativas.popleft()
        tentativas.append(agora)
        if len(tentativas) >= self._max:
            self._bloqueadas[chave] = agora + self._bloqueio
            del self._tentativas[chave]

    def limpar(self, chave: str) -> None:
        self._tentativas.pop(chave, None)
        self._bloqueadas.pop(chave, None)
