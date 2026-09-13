"""
Settings centralizados via pydantic-settings (RNF07: nada fixo em código).
Carrega variáveis de ambiente do arquivo .env na raiz de backend/.
"""
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:admin@localhost:5432/sgopi"
    database_echo: bool = False

    # RNF02*: JWT de turno (8 h), CORS por lista de origens
    jwt_secret_key: str = "dev-secret-insecure-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_in_hours: int = 8
    # NoDecode: o valor do .env chega como string "a,b,c" ao validador abaixo (sem tentar json.loads)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]

    # RNF04*: idade máxima da posição GPS para ser considerada válida
    telemetria_max_idade_segundos: int = 60
    # RF16: simulador de telemetria
    simulador_intervalo_segundos: float = 1.0
    simulador_raio_metros: float = 150.0
    # RF18: quantidade de sugestões de viatura
    despacho_qtd_sugestoes: int = 3

    log_json: bool = True
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        """Aceita lista separada por vírgula (formato do .env) ou JSON (["a","b"])."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json

                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


settings = Settings()
