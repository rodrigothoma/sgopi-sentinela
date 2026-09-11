"""
Testes unitários de Settings (infrastructure/config.py).

Não sobem servidor nem conectam banco real — só validam a montagem da
URL de conexão a partir de variáveis de ambiente.
"""
from infrastructure.config import Settings


def test_sqlalchemy_url_e_montada_a_partir_das_variaveis_postgres(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(
        postgres_user="agente",
        postgres_password="senha123",
        postgres_db="sgopi_teste",
        postgres_host="db",
        postgres_port=5433,
    )

    assert settings.sqlalchemy_url == (
        "postgresql+asyncpg://agente:senha123@db:5433/sgopi_teste"
    )


def test_database_url_sobrepoe_as_variaveis_postgres_individuais():
    settings = Settings(
        database_url="postgresql+asyncpg://outro:outro@host-externo:5432/outro_db",
        postgres_user="ignorado",
        postgres_password="ignorado",
        postgres_db="ignorado",
        postgres_host="ignorado",
        postgres_port=1,
    )

    assert settings.sqlalchemy_url == (
        "postgresql+asyncpg://outro:outro@host-externo:5432/outro_db"
    )


def test_settings_tem_defaults_utilizaveis_sem_env_file():
    settings = Settings(_env_file=None)

    assert settings.postgres_host == "localhost"
    assert settings.postgres_port == 5432
    assert settings.db_health_timeout == 3.0
    assert settings.sqlalchemy_url.startswith("postgresql+asyncpg://")
