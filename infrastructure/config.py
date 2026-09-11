"""
Configuração da aplicação: leitura de variáveis de ambiente (.env).

Este módulo faz parte de `infrastructure/`, então PODE depender de libs
externas (pydantic-settings) — só `domain/` e `application/` têm a
restrição de não importar nada fora da stdlib.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Variáveis de ambiente da aplicação.

    Todas têm um default que funciona com o `compose.yaml` do próprio
    repositório, então a aplicação sobe mesmo sem um arquivo `.env`
    (útil em CI e para quem ainda não copiou o `.env.example`).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"

    postgres_user: str = "sgopi"
    postgres_password: str = "sgopi"
    postgres_db: str = "sgopi"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Sobrepõe as variáveis POSTGRES_* acima quando definida. Útil para
    # apontar para um banco externo (ex: em CI) sem editar as demais.
    database_url: str | None = None

    # Timeout (em segundos) do SELECT 1 do endpoint /health.
    db_health_timeout: float = 3.0

    @property
    def sqlalchemy_url(self) -> str:
        """URL de conexão assíncrona (driver asyncpg) usada pela engine."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Settings cacheadas — lidas do ambiente uma única vez por processo."""
    return Settings()
