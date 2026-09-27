"""Settings: CORS_ORIGINS aceita lista separada por vírgula no .env (regressão do erro de json.loads)."""
from infrastructure.config.settings import Settings


def test_cors_origins_por_virgula(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, http://localhost:3001")
    assert Settings(_env_file=None).cors_origins == ["http://localhost:3000", "http://localhost:3001"]


def test_cors_origins_json(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["http://a", "http://b"]')
    assert Settings(_env_file=None).cors_origins == ["http://a", "http://b"]


def test_cors_origins_default(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert "http://localhost:3000" in Settings(_env_file=None).cors_origins


def test_simulador_destino_defaults():
    s = Settings(_env_file=None)
    assert s.simulador_passo_destino_metros == 300.0
    assert s.simulador_raio_chegada_metros == 50.0
    assert s.simulador_jitter_chegada_metros == 5.0
    assert s.simulador_roteador_url == ""  # vazio = linha reta, sem rede


def test_gerador_ocorrencias_desligado_por_padrao():
    """Issue #55: opt-in — nunca ativo sem .env explícito (anti-flakiness)."""
    s = Settings(_env_file=None)
    assert s.gerador_ocorrencias_ligado is False
    assert s.gerador_ocorrencias_intervalo_segundos == 120.0


def test_gerador_ocorrencias_intervalo_minimo():
    """Issue #55 ajuste 3: intervalo < 1s é inválido."""
    import pytest

    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(_env_file=None, gerador_ocorrencias_intervalo_segundos=0.5)
