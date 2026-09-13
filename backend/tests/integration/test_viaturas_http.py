"""Integração HTTP: frota, telemetria e simulador (RF15, RF16)."""
import asyncio
from datetime import UTC, datetime, timedelta

from tests.integration.helpers import auth


async def _cadastrar(client, h, prefixo="VTR-01", placa="IAB1A23"):
    r = await client.post("/v1/viaturas", json={"prefixo": prefixo, "placa": placa}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


async def test_cadastro_duplicado_409_e_listagem(client):
    ho = await auth(client, "operador")
    v = await _cadastrar(client, ho)
    assert v["situacao"] == "DISPONIVEL" and v["sinal"] == "SEM_POSICAO"
    r = await client.post("/v1/viaturas", json={"prefixo": "vtr-01", "placa": "XXX0000"}, headers=ho)
    assert r.status_code == 409 and r.json()["code"] == "viatura.prefixo_duplicado"
    r = await client.get("/v1/viaturas", headers=await auth(client, "agente"))
    assert r.status_code == 200 and [x["prefixo"] for x in r.json()] == ["VTR-01"]
    r = await client.post("/v1/viaturas", json={"prefixo": "VTR-02", "placa": "YYY0000"}, headers=await auth(client, "agente"))
    assert r.status_code == 403


async def test_situacao_manual(client):
    ho = await auth(client, "operador")
    v = await _cadastrar(client, ho)
    r = await client.patch(f"/v1/viaturas/{v['id']}/situacao", json={"situacao": "INDISPONIVEL"}, headers=ho)
    assert r.status_code == 200 and r.json()["situacao"] == "INDISPONIVEL"
    r = await client.patch(f"/v1/viaturas/{v['id']}/situacao", json={"situacao": "OPERANDO"}, headers=ho)
    assert r.status_code == 422 and r.json()["code"] == "viatura.situacao_manual_invalida"


async def test_telemetria_aceita_dentro_da_janela_e_rejeita_fora(client):
    ho = await auth(client, "operador")
    v = await _cadastrar(client, ho)
    agora = datetime.now(UTC)
    r = await client.post("/v1/telemetria/posicoes", json={"viatura_id": v["id"], "latitude": -29.78, "longitude": -55.79, "registrada_em": agora.isoformat()}, headers=ho)
    assert r.status_code == 200 and r.json()["sinal"] == "OK"
    r = await client.post("/v1/telemetria/posicoes", json={"viatura_id": v["id"], "latitude": 0, "longitude": 0, "registrada_em": (agora - timedelta(minutes=5)).isoformat()}, headers=ho)
    assert r.status_code == 422 and r.json()["code"] == "telemetria.timestamp_fora_da_janela"
    r = await client.get("/v1/viaturas", headers=ho)
    assert r.json()[0]["latitude"] == -29.78  # posição anterior mantida


async def test_simulador_liga_desliga_via_api(app, client, session_factory):
    from infrastructure.di import get_simulador, montar_simulador

    sim = montar_simulador(session_factory, intervalo_segundos=0.02, semente=1)
    app.dependency_overrides[get_simulador] = lambda: sim
    ho = await auth(client, "operador")
    await _cadastrar(client, ho, "VTR-01", "AAA0001")
    await _cadastrar(client, ho, "VTR-02", "AAA0002")

    r = await client.get("/v1/simulador", headers=ho)
    assert r.json()["ligado"] is False
    r = await client.post("/v1/simulador/ligar", headers=ho)
    assert r.status_code == 200 and r.json()["ligado"] is True
    await asyncio.sleep(0.12)
    r = await client.post("/v1/simulador/desligar", headers=ho)
    assert r.json()["ligado"] is False and r.json()["ticks"] >= 2
    r = await client.get("/v1/viaturas", headers=ho)
    assert all(v["sinal"] == "OK" and v["latitude"] is not None for v in r.json())
    r = await client.post("/v1/simulador/ligar", headers=await auth(client, "agente"))
    assert r.status_code == 403
