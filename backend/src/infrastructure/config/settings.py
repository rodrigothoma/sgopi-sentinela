"""
Settings centralizados via pydantic-settings.
Carrega variáveis de ambiente do arquivo .env na raiz de backend/.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:admin@localhost:5432/sgopi"
    jwt_secret_key: str = "dev-secret-insecure"
    jwt_expires_in_hours: int = 24
    disable_request_limits: bool = False


settings = Settings()
