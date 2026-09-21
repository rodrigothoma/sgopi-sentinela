"""Integração HTTP: fluxo ponta a ponta do MVP (registrar → validar → sugerir → despachar → encerrar) e atomicidade (RF02, RNF03)."""
from datetime import UTC, datetime

from sqlalchemy import select

from infrastructure.database.models import OcorrenciaModel, OrdemDespachoModel, ViaturaModel
from tests.integration.helpers import auth, registrar


async def _frota(client, ho):
    ids = {}
    for prefixo, lat, lon in [("VTR-01", -29.80, -55.80), ("VTR-02", -29.7833, -55.7919), ("VTR-03", -29.70, -55.70)]:
        v = (await client.post("/v1/viaturas", json={"prefixo": prefixo, "placa": f"P{prefixo[-2:]}0000"}, headers=ho)).json()
        await client.post("/v1/telemetria/posicoes", json={"viatura_id": v["id"], "latitude": lat, "longitude": lon, "registrada_em": datetime.now(UTC).isoformat()}, headers=ho)
        ids[prefixo] = v["id"]
    return ids


async def _validada(client):
    o = await registrar(client, await auth(client, "agente"))
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=await auth(client, "delegado"))
    assert r.status_code == 200
    return o["ocorrencia_id"]


async def test_fluxo_mvp_ponta_a_ponta(client, session):
    ho = await auth(client, "operador")
    frota = await _frota(client, ho)
    oid = await _validada(client)

    r = await client.get(f"/v1/ocorrencias/{oid}/sugestoes-viaturas", headers=ho)
    assert r.status_code == 200
    sug = r.json()
    assert [s["viatura"]["prefixo"] for s in sug["sugestoes"]] == ["VTR-02", "VTR-01", "VTR-03"] and not sug["sem_elegiveis"]
    assert sug["sugestoes"][0]["distancia_km"] == 0.0

    r = await client.post("/v1/despachos", json={"ocorrencia_id": oid, "viatura_id": frota["VTR-02"], "observacoes": "Código 3"}, headers=ho)
    assert r.status_code == 201, r.text
    ordem = r.json()
    assert ordem["numero"].startswith("OD-") and ordem["ativa"] and ordem["observacoes"] == "Código 3"
    # critério 5 do MVP: data/hora, operador, viatura, ocorrência
    assert all(ordem[k] for k in ("criada_em", "operador_id", "viatura_id", "ocorrencia_id"))

    r = await client.get(f"/v1/ocorrencias/{oid}", headers=ho)
    assert r.json()["status"] == "EM_ATENDIMENTO"
    r = await client.get("/v1/viaturas", headers=ho)
    assert {v["prefixo"]: v["situacao"] for v in r.json()}["VTR-02"] == "EM_DESLOCAMENTO"
    r = await client.get("/v1/despachos", params={"ocorrencia_id": oid, "somente_ativas": "true"}, headers=await auth(client, "delegado"))
    assert len(r.json()) == 1

    # viatura despachada some das sugestões de outra ocorrência
    oid2 = await _validada(client)
    r = await client.get(f"/v1/ocorrencias/{oid2}/sugestoes-viaturas", headers=ho)
    assert [s["viatura"]["prefixo"] for s in r.json()["sugestoes"]] == ["VTR-01", "VTR-03"]
    r = await client.post("/v1/despachos", json={"ocorrencia_id": oid2, "viatura_id": frota["VTR-02"]}, headers=ho)
    assert r.status_code == 409 and r.json()["code"] == "despacho.viatura_indisponivel"

    r = await client.post(f"/v1/ocorrencias/{oid}/encerrar", json={"desfecho": "Atendimento concluído sem intercorrências."}, headers=ho)
    assert r.status_code == 200 and r.json()["status"] == "ENCERRADA"
    r = await client.get("/v1/viaturas", headers=ho)
    assert {v["prefixo"]: v["situacao"] for v in r.json()}["VTR-02"] == "DISPONIVEL"
    r = await client.get("/v1/despachos", params={"ocorrencia_id": oid}, headers=ho)
    assert r.json()[0]["ativa"] is False and r.json()[0]["encerrada_em"]
    # RF02 aceite 2: viatura volta a aparecer nas sugestões
    r = await client.get(f"/v1/ocorrencias/{oid2}/sugestoes-viaturas", headers=ho)
    assert [s["viatura"]["prefixo"] for s in r.json()["sugestoes"]] == ["VTR-02", "VTR-01", "VTR-03"]


async def test_sem_elegiveis_permite_despacho_manual(client):
    ho = await auth(client, "operador")
    v = (await client.post("/v1/viaturas", json={"prefixo": "VTR-07", "placa": "P070000"}, headers=ho)).json()
    oid = await _validada(client)
    r = await client.get(f"/v1/ocorrencias/{oid}/sugestoes-viaturas", headers=ho)
    assert r.json()["sem_elegiveis"] and r.json()["disponiveis_sem_posicao"][0]["prefixo"] == "VTR-07"
    r = await client.post("/v1/despachos", json={"ocorrencia_id": oid, "viatura_id": v["id"]}, headers=ho)
    assert r.status_code == 201


async def test_despacho_e_atomico_em_falha_no_meio(app, client, session):
    from infrastructure.di import get_gerador_numero_ordem

    class GeradorQuebrado:
        async def proximo(self, ano):
            raise RuntimeError("sequência indisponível")

    ho = await auth(client, "operador")
    frota = await _frota(client, ho)
    oid = await _validada(client)
    app.dependency_overrides[get_gerador_numero_ordem] = lambda: GeradorQuebrado()
    r = await client.post("/v1/despachos", json={"ocorrencia_id": oid, "viatura_id": frota["VTR-01"]}, headers=ho)
    assert r.status_code == 500 and r.json()["code"] == "generic.internal_error"
    assert r.json()["request_id"] and r.headers["X-Request-ID"] == r.json()["request_id"]

    import uuid

    assert (await session.get(OcorrenciaModel, uuid.UUID(oid))).status == "VALIDADA"
    assert (await session.get(ViaturaModel, uuid.UUID(frota["VTR-01"]))).situacao == "DISPONIVEL"
    assert (await session.execute(select(OrdemDespachoModel))).scalars().all() == []


async def test_encerrar_exige_desfecho_e_papel(client):
    ho = await auth(client, "operador")
    frota = await _frota(client, ho)
    oid = await _validada(client)
    await client.post("/v1/despachos", json={"ocorrencia_id": oid, "viatura_id": frota["VTR-01"]}, headers=ho)
    r = await client.post(f"/v1/ocorrencias/{oid}/encerrar", json={"desfecho": "   "}, headers=ho)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.desfecho_vazio"
    r = await client.post(f"/v1/ocorrencias/{oid}/encerrar", json={"desfecho": "ok"}, headers=await auth(client, "agente"))
    assert r.status_code == 403
