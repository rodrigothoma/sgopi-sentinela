"""Fixtures dos testes de contrato: a mesma bateria roda contra a fake e contra o SQLAlchemy.

A fábrica de sessões abre uma "sessão" por bloco ``async with``: no SQLAlchemy é uma sessão real
(repositório novo, transação própria); na fake é sempre a mesma instância, que guarda o
estado como um banco compartilhado. Duas sessões abertas ao mesmo tempo simulam dois
usuários concorrentes.
"""
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class Sessao:
    repo: Any
    _commit: Callable[[], Any]

    async def commit(self) -> None:
        await self._commit()


async def _sem_efeito() -> None:
    return None


AbrirSessao = Callable[[], Any]  # async context manager que entrega uma Sessao


def sessoes_fake(repo: Any) -> AbrirSessao:
    @asynccontextmanager
    async def abrir() -> AsyncIterator[Sessao]:
        yield Sessao(repo, _sem_efeito)

    return abrir


def sessoes_sqlalchemy(session_factory: Any, fabrica_repo: Callable[[Any], Any]) -> AbrirSessao:
    @asynccontextmanager
    async def abrir() -> AsyncIterator[Sessao]:
        async with session_factory() as s:
            yield Sessao(fabrica_repo(s), s.commit)
            await s.rollback()

    return abrir


IMPLEMENTACOES = pytest.mark.parametrize("implementacao", ["fake", "sqlalchemy"])
