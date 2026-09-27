"""
Testes E2E de API (issues #21/#22): rodam contra o backend REAL em pé
(``uvicorn`` em :8000, com SQLite ou Postgres tanto faz), não contra ASGI em memória.

São pulados automaticamente quando o servidor não está no ar, então a suíte
padrão (``uv run pytest``) continua verde para quem só desenvolve. Para rodar
apenas eles: ``uv run pytest -m e2e``.
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import httpx
import pytest

BASE_URL = os.environ.get("SGOPI_E2E_BASE_URL", "http://localhost:8000")
SENHA = "Senha@123"
# Em CI (SGOPI_E2E_STRICT=1) o backend TEM que estar no ar: falha com
# diagnóstico claro em vez de Connection refused espalhado. Localmente,
# mantém o comportamento antigo de pular quando ninguém subiu o servidor.
STRICT = os.environ.get("SGOPI_E2E_STRICT", "").strip().lower() in {"1", "true", "yes"}


def _servidor_no_ar() -> bool:
    try:
        return httpx.get(f"{BASE_URL}/health", timeout=2).status_code == 200
    except Exception:
        return False


def pytest_collection_modifyitems(items) -> None:
    """Marca como `e2e` só os testes deste diretório (`pytestmark` em conftest.py é ignorado)."""
    for item in items:
        if item.path.parent.name == "e2e":
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session", autouse=True)
def garantir_backend_no_ar():
    """Falha com diagnóstico claro (CI) ou pula (dev local) se o backend caiu."""
    if _servidor_no_ar():
        return
    mensagem = (
        f"Backend E2E indisponível em {BASE_URL}/health. "
        "Suba com: uv run uvicorn --app-dir src main:app --reload "
        "(após `uv run alembic upgrade head` + `uv run python -m scripts.seed`)."
    )
    if STRICT:
        pytest.fail(mensagem)
    pytest.skip(mensagem)


@pytest.fixture
def client() -> httpx.Client:
    with httpx.Client(base_url=BASE_URL, timeout=10) as c:
        yield c


def token_de(client: httpx.Client, login: str) -> str:
    r = client.post("/v1/auth/login", json={"login": login, "senha": SENHA})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth(client: httpx.Client):
    """Factory: auth(client, 'agente') → headers com Bearer token."""

    def _auth(login: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token_de(client, login)}"}

    return _auth


def corpo_ocorrencia(**overrides) -> dict:
    corpo = {
        "natureza": "Furto",
        "descricao": "Furto de veículo em via pública, sem violência (E2E).",
        "localizacao": "Av. Brasil, 500 — Alegrete/RS",
        "latitude": -29.7833,
        "longitude": -55.7919,
        "data_hora_fato": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "envolvidos": [{"nome": "Maria Teste", "tipo": "VITIMA"}],
        "tipificacoes": [{"artigo": "Art. 155 CP", "descricao": "Furto simples"}],
    }
    corpo.update(overrides)
    return corpo


@pytest.fixture
def ocorrencia_registrada(client: httpx.Client, auth) -> dict:
    r = client.post("/v1/ocorrencias", json=corpo_ocorrencia(), headers=auth("agente"))
    assert r.status_code == 201, r.text
    return r.json()
