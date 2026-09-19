"""
Fixtures de integração: SQLite em memória (aiosqlite) com o esquema dos models.

Docker/Postgres não é exigido para a suíte; o esquema Postgres é validado por
``alembic check``.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from infrastructure.database.connection import Base, get_session
import infrastructure.database.models as models  # noqa: F401

IDS = {
    "agente": UUID("00000000-0000-0000-0000-000000000001"),
    "delegado": UUID("00000000-0000-0000-0000-000000000002"),
    "operador": UUID("00000000-0000-0000-0000-000000000003"),
    "agente2": UUID("00000000-0000-0000-0000-000000000004"),
}
PAPEIS = {"agente": "AGENTE", "delegado": "DELEGADO", "operador": "OPERADOR_CENTRAL", "agente2": "AGENTE"}
SENHA_PADRAO = "Senha@123"


@pytest.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as s:
        yield s


@pytest.fixture
async def usuarios(session_factory):
    """Semeia um usuário por papel (RF12) com senha argon2 real."""
    from adapters.outbound.seguranca.hasher_argon2 import HasherArgon2

    hasher = HasherArgon2()
    hash_ = hasher.gerar_hash(SENHA_PADRAO)
    async with session_factory() as s:
        for login, uid in IDS.items():
            s.add(models.UsuarioModel(id=uid, nome=login.title(), login=login, senha_hash=hash_, papel=PAPEIS[login], ativo=True))
        s.add(models.UsuarioModel(nome="Inativo", login="inativo", senha_hash=hash_, papel="AGENTE", ativo=False))
        await s.commit()
    return IDS


@pytest.fixture
async def app(session_factory, usuarios):
    from main import criar_app

    application = criar_app()

    async def _get_session():
        async with session_factory() as s:
            yield s

    application.dependency_overrides[get_session] = _get_session
    return application


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as c:
        yield c
