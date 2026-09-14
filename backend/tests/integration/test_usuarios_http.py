"""Integração HTTP: efetivo ativo para a tela inicial (RF12)."""
from tests.integration.helpers import auth


async def test_lista_efetivo_ativo_sem_credenciais(client):
    r = await client.get("/v1/usuarios", headers=await auth(client, "agente"))
    assert r.status_code == 200, r.text
    itens = r.json()
    logins = [u["login"] for u in itens]
    assert logins == ["agente", "agente2", "delegado", "operador"]  # inativo não aparece
    assert all(set(u) == {"id", "nome", "login", "papel"} for u in itens)
    papeis = {u["login"]: u["papel"] for u in itens}
    assert papeis["delegado"] == "DELEGADO" and papeis["operador"] == "OPERADOR_CENTRAL"


async def test_exige_token(client):
    assert (await client.get("/v1/usuarios")).status_code == 401
