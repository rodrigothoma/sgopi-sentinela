"""
Máquina de estados declarativa: uma tabela ``(estado, operação) -> estado`` por agregado.

As regras de transição ficam numa estrutura só, legível e testável, em vez de espalhadas
em ``if status not in (...)`` pelos métodos. Uma operação que exige um estado sem mudá-lo
(p.ex. vincular ocorrência a inquérito em andamento) é um laço ``(S, op) -> S``.
A máquina não lança exceções: cada entidade decide o erro (tipo e chave i18n) da recusa.
"""
from __future__ import annotations

from collections.abc import Mapping
from enum import Enum


class MaquinaEstados[S: Enum, Op: Enum]:
    def __init__(self, transicoes: Mapping[tuple[S, Op], S]) -> None:
        self._transicoes: dict[tuple[S, Op], S] = dict(transicoes)

    def proximo(self, atual: S, operacao: Op) -> S | None:
        """Estado de destino, ou ``None`` se a operação não é permitida no estado atual."""
        return self._transicoes.get((atual, operacao))

    def permite(self, atual: S, operacao: Op) -> bool:
        return (atual, operacao) in self._transicoes

    def origens(self, operacao: Op) -> frozenset[S]:
        """Estados a partir dos quais a operação é permitida."""
        return frozenset(origem for origem, op in self._transicoes if op == operacao)

    def destinos(self, operacao: Op) -> frozenset[S]:
        return frozenset(destino for (_, op), destino in self._transicoes.items() if op == operacao)
