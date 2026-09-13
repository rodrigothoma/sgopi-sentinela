"""
Engine assíncrono e sessão SQLAlchemy.
Fornece get_db() para injeção via FastAPI Depends.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from infrastructure.config.settings import settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os models SQLAlchemy."""


engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependência FastAPI que fornece uma sessão async por request."""
    async with AsyncSessionLocal() as session:
        yield session
