"""
Testes E2E de API (issues #21/#22): rodam contra o backend REAL em pé
(``uvicorn`` em :8000, com SQLite ou Postgres tanto faz), não contra ASGI em memória.

São pulados automaticamente quando o servidor não está no ar, então a suíte
padrão (``uv run pytest``) continua verde para quem só desenvolve. Para rodar
apenas eles: ``uv run pytest -m e2e``.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

BASE_URL = "http://localhost:8000"
SENHA = "Senha@123"


def _servidor_no_ar() -> bool:
    try:
        return httpx.get(f"{BASE_URL}/health", timeout=2).status_code == 200
    except Exception:
        return False


pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not _servidor_no_ar(), reason="backend não está no ar em :8000")]


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
        "envolvidos": [{"nome": "Maria E2E", "tipo": "VITIMA"}],
        "tipificacoes": [{"artigo": "Art. 155 CP", "descricao": "Furto simples"}],
    }
    corpo.update(overrides)
    return corpo


@pytest.fixture
def ocorrencia_registrada(client: httpx.Client, auth) -> dict:
    r = client.post("/v1/ocorrencias", json=corpo_ocorrencia(), headers=auth("agente"))
    assert r.status_code == 201, r.text
    return r.json()
