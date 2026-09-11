"""
Configuração do banco: engine assíncrona, sessão e Base declarativa.

Como `infrastructure/config.py`, este módulo pode importar SQLAlchemy
livremente — a regra de "nenhuma dependência externa" vale só para
`domain/` e `application/`.

T4 (persistência) herda os modelos SQLAlchemy de `Base` e usa
`get_session()` no DAO; T5 (API) usa `get_session()` via `Depends`.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from infrastructure.config import get_settings


class Base(DeclarativeBase):
    """Classe base declarativa para os modelos SQLAlchemy (usar em T4)."""


@lru_cache
def get_engine() -> AsyncEngine:
    """
    Engine assíncrona, criada preguiçosamente e cacheada por processo.

    `pool_pre_ping=True` descarta conexões mortas antes de reusá-las
    (ex: banco reiniciado) em vez de estourar erro na primeira query.
    """
    settings = get_settings()
    return create_async_engine(settings.sqlalchemy_url, pool_pre_ping=True)


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependência FastAPI: entrega uma sessão por requisição e a fecha ao final."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session
