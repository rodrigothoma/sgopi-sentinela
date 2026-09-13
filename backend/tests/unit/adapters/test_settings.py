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
