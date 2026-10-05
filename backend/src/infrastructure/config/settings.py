"""
Settings centralizados via pydantic-settings (12-Factor: nada fixo em código).
Carrega variáveis de ambiente do arquivo .env na raiz de backend/.
"""
from __future__ import annotations

from typing import Annotated
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

SEGREDO_JWT_DEV = "dev-secret-insecure-change-me-local-only"  # ≥ 32 bytes: HS256 (RFC 7518 §3.2)
TAMANHO_MINIMO_SEGREDO_JWT = 32
# Placeholders de exemplo (.env.example) que nunca podem chegar a produção
_MARCADORES_SEGREDO_EXEMPLO = ("troque", "change-me", "changeme", "exemplo", "example")
_SENHAS_BANCO_PADRAO = {"admin", "postgres", "senha", "password"}
_HOSTS_LOCAIS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:admin@localhost:5433/sgopi"
    database_echo: bool = False

    # RNF02*: JWT de turno (8 h), CORS por lista de origens
    jwt_secret_key: str = SEGREDO_JWT_DEV
    jwt_algorithm: str = "HS256"
    jwt_expires_in_hours: int = 8
    # NoDecode: o valor do .env chega como string "a,b,c" ao validador abaixo (sem tentar json.loads)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]

    # RNF02*: proteção contra força bruta no login (falhas por login+IP) e limite de
    # comunicações públicas por IP (Delegacia Online, sem autenticação)
    # X-Forwarded-For só é aceito quando a conexão vem de um destes proxies (senão o
    # cliente poderia forjar o IP e burlar limites e auditoria)
    proxies_confiaveis: Annotated[list[str], NoDecode] = ["127.0.0.1", "::1"]
    login_max_tentativas: int = Field(default=5, ge=1)
    login_janela_segundos: float = Field(default=900.0, gt=0.0)
    login_bloqueio_segundos: float = Field(default=900.0, gt=0.0)
    registro_publico_max_por_ip: int = Field(default=20, ge=1)
    registro_publico_janela_segundos: float = Field(default=600.0, gt=0.0)
    registro_publico_bloqueio_segundos: float = Field(default=600.0, gt=0.0)
    # Consultas públicas (protocolo + código, autenticação de documento): cota por IP contra enumeração
    consulta_publica_max_por_ip: int = Field(default=30, ge=1)
    consulta_publica_janela_segundos: float = Field(default=600.0, gt=0.0)
    consulta_publica_bloqueio_segundos: float = Field(default=600.0, gt=0.0)

    # N12: segredo das credenciais HMAC dos rastreadores (vazio = ingestão por dispositivo desligada)
    telemetria_segredo_dispositivos: str = ""

    # RNF04*: idade máxima da posição GPS para ser considerada válida
    telemetria_max_idade_segundos: int = 60
    # RF02: simulador de telemetria
    simulador_intervalo_segundos: float = 1.0
    simulador_raio_metros: float = 150.0
    # RF02: simulador com destino — vazio em roteador = linha reta, sem rede.
    # Metros percorridos por tick ao navegar até a ocorrência: 35 m a cada 1 s ≈ 126 km/h,
    # o bastante para o deslocamento ser visível no painel (300 m/tick ≈ 1080 km/h).
    simulador_passo_destino_metros: float = 35.0
    simulador_raio_chegada_metros: float = 50.0
    simulador_jitter_chegada_metros: float = 5.0
    simulador_roteador_url: str = ""
    # services externos demoram a responder com cache frio; o timeout curto derruba a frota inteira
    simulador_roteador_timeout_segundos: float = Field(default=5.0, gt=0.0)
    # RF01: gerador automático de ocorrências fictícias p/ demo — opt-in, nunca ativo em testes
    gerador_ocorrencias_ligado: bool = False
    gerador_ocorrencias_intervalo_segundos: float = Field(default=120.0, ge=1.0)
    # RF02: velocidade da viatura despachada no simulador (deslocamento em linha reta até a ocorrência)
    simulador_velocidade_kmh: float = 120.0
    # RF02: a que distância da ocorrência a telemetria considera a viatura "no local"
    despacho_raio_chegada_metros: float = 50.0
    # RF02: quantidade de sugestões de viatura
    despacho_qtd_sugestoes: int = 3
    # RF02/RF18/RF19/RNF04: despacho e encerramento automáticos — opt-in, nunca em testes
    despacho_automatico_ligado: bool = False
    orquestrador_intervalo_segundos: float = Field(default=5.0, ge=1.0)
    janela_carencia_segundos: int = 20
    tempo_atendimento_segundos: int = 45

    # RF01: evidências digitais armazenadas localmente atrás de uma porta
    evidencias_diretorio: str = "storage/evidencias"
    evidencias_tamanho_maximo_bytes: int = 10 * 1024 * 1024

    # RF09 / UC12: Notificações por e-mail (alerta de vencimento de medida protetiva)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_usuario: str = ""
    smtp_senha: str = ""
    smtp_remetente: str = "sentinela@seguranca.gov.br"
    smtp_usar_tls: bool = True

    log_json: bool = True
    log_level: str = "INFO"

    @field_validator("cors_origins", "proxies_confiaveis", mode="before")
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

    @model_validator(mode="after")
    def _validar_seguranca(self) -> Settings:
        """Fail-fast: em produção a aplicação não sobe com configuração de desenvolvimento (RNF02)."""
        if not self.jwt_secret_key or not self.jwt_secret_key.strip():
            self.jwt_secret_key = SEGREDO_JWT_DEV
        if self.is_production:
            problemas = self._problemas_de_producao()
            if problemas:
                raise ValueError("Configuração insegura para app_env=production: " + "; ".join(problemas))
        return self

    def _problemas_de_producao(self) -> list[str]:
        problemas: list[str] = []
        segredo = self.jwt_secret_key.lower()
        if (
            self.jwt_secret_key == SEGREDO_JWT_DEV
            or len(self.jwt_secret_key) < TAMANHO_MINIMO_SEGREDO_JWT
            or any(m in segredo for m in _MARCADORES_SEGREDO_EXEMPLO)
        ):
            problemas.append(f"jwt_secret_key precisa ser um segredo aleatório com ≥ {TAMANHO_MINIMO_SEGREDO_JWT} caracteres")
        if (urlsplit(self.database_url).password or "").lower() in _SENHAS_BANCO_PADRAO:
            problemas.append("database_url usa uma senha padrão")
        if any(o == "*" or urlsplit(o).hostname in _HOSTS_LOCAIS for o in self.cors_origins):
            problemas.append("cors_origins não pode conter '*' nem origens locais")
        if self.smtp_host and not self.smtp_usar_tls:
            problemas.append("smtp_usar_tls deve ser true quando há servidor SMTP")
        if self.despacho_automatico_ligado or self.gerador_ocorrencias_ligado:
            problemas.append("despacho automático e gerador de ocorrências são recursos de demonstração")
        return problemas

    @property
    def telemetria_humana_permitida(self) -> bool:
        """Fora de produção, Operador/Supervisor podem injetar posições (testes, demonstração)."""
        return not self.is_production

    @property
    def simulador_habilitado(self) -> bool:
        """O simulador de telemetria move viaturas reais: só fora de produção."""
        return not self.is_production

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


settings = Settings()
