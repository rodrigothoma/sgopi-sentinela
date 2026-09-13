"""
Engine assíncrono e fábrica de sessões SQLAlchemy.
``get_session`` é a única dependência FastAPI que os adapters conhecem; os
testes de integração a substituem por uma sessão SQLite em memória.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from infrastructure.config.settings import settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os models SQLAlchemy."""


def criar_engine(url: str | None = None, echo: bool | None = None) -> AsyncEngine:
    return create_async_engine(url or settings.database_url, echo=settings.database_echo if echo is None else echo)


engine: AsyncEngine = criar_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependência FastAPI: uma sessão async por request (a UoW decide o commit)."""
    async with AsyncSessionLocal() as session:
        yield session
