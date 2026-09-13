"""Helpers HTTP compartilhados pelos testes de integração."""
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from tests.integration.conftest import SENHA_PADRAO


async def token_de(client: AsyncClient, login: str) -> str:
    r = await client.post("/v1/auth/login", json={"login": login, "senha": SENHA_PADRAO})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def auth(client: AsyncClient, login: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {await token_de(client, login)}"}


def corpo_ocorrencia(**overrides) -> dict:
    corpo = {
        "natureza": "Furto",
        "descricao": "Furto de veículo em via pública, sem violência.",
        "localizacao": "Av. Brasil, 500 — Alegrete/RS",
        "latitude": -29.7833,
        "longitude": -55.7919,
        "data_hora_fato": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        "envolvidos": [{"nome": "Maria", "tipo": "VITIMA"}],
        "tipificacoes": [{"artigo": "Art. 155 CP", "descricao": "Furto simples"}],
    }
    corpo.update(overrides)
    return corpo


async def registrar(client: AsyncClient, headers: dict, **overrides) -> dict:
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(**overrides), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
