"""Integração HTTP ponta a ponta: fila do Delegado, decisões, correção/reenvio, auditoria (RF01, RF04*, RNF03)."""
from sqlalchemy import select

from infrastructure.database.models import RegistroAuditoriaModel
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, registrar


async def test_fila_do_delegado_ordenada_e_filtrada(client):
    ha = await auth(client, "agente")
    o1 = await registrar(client, ha)
    o2 = await registrar(client, ha)
    hd = await auth(client, "delegado")
    await client.post(f"/v1/ocorrencias/{o2['ocorrencia_id']}/validar", headers=hd)

    r = await client.get("/v1/ocorrencias", params={"status": "AGUARDANDO_REVISAO"}, headers=hd)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] == 1 and corpo["itens"][0]["ocorrencia_id"] == o1["ocorrencia_id"]
    r = await client.get("/v1/ocorrencias", params=[("status", "AGUARDANDO_REVISAO"), ("status", "VALIDADA")], headers=hd)
    assert [i["ocorrencia_id"] for i in r.json()["itens"]] == [o1["ocorrencia_id"], o2["ocorrencia_id"]]
    r = await client.get("/v1/ocorrencias", params={"status": "XPTO"}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.status_invalido"


async def test_agente_ve_apenas_as_proprias_e_operador_ve_cpf_mascarado(client):
    o = await registrar(client, await auth(client, "agente"), envolvidos=[{"nome": "X", "tipo": "SUSPEITO", "documento": "123.456.789-09"}])
    r = await client.get("/v1/ocorrencias", headers=await auth(client, "agente2"))
    assert r.json()["total"] == 0
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}", headers=await auth(client, "agente2"))
    assert r.status_code == 403
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}", headers=await auth(client, "operador"))
    assert r.status_code == 200 and r.json()["envolvidos"][0]["documento"] == "***.***.789-**"
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}", headers=await auth(client, "delegado"))
    assert r.json()["envolvidos"][0]["documento"] == "123.456.789-09"


async def test_detalhe_404(client):
    r = await client.get("/v1/ocorrencias/00000000-0000-0000-0000-00000000dead", headers=await auth(client, "delegado"))
    assert r.status_code == 404 and r.json()["code"] == "ocorrencia.not_found"


async def test_somente_delegado_valida_403_auditado(client, session):
    o = await registrar(client, await auth(client, "agente"))
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=await auth(client, "operador"))
    assert r.status_code == 403
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=await auth(client, "delegado"))
    assert r.status_code == 200 and r.json()["status"] == "VALIDADA" and r.json()["validada_por_id"] == str(IDS["delegado"])
    ops = (await session.execute(select(RegistroAuditoriaModel.operacao))).scalars().all()
    assert "auth.acesso_negado" in ops and "ocorrencia.validar" in ops


async def test_validar_duas_vezes_422(client):
    o = await registrar(client, await auth(client, "agente"))
    hd = await auth(client, "delegado")
    await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=hd)
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.invalid_transition"
    assert r.json()["extra"]["status_atual"] == "VALIDADA"


async def test_devolver_corrigir_reenviar_validar(client):
    ha, hd = await auth(client, "agente"), await auth(client, "delegado")
    o = await registrar(client, ha)
    oid = o["ocorrencia_id"]

    r = await client.post(f"/v1/ocorrencias/{oid}/devolver", json={"justificativa": "curta"}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.justificativa_curta"
    r = await client.post(f"/v1/ocorrencias/{oid}/devolver", json={"justificativa": "Faltam dados do veículo."}, headers=hd)
    assert r.status_code == 200 and r.json()["status"] == "EM_CORRECAO"

    # o agente autor vê a justificativa
    r = await client.get(f"/v1/ocorrencias/{oid}", headers=ha)
    assert r.json()["justificativa_revisao"] == "Faltam dados do veículo."

    # outro agente não pode corrigir
    r = await client.put(f"/v1/ocorrencias/{oid}", json={"descricao": "Descrição complementada com placa ABC-1234."}, headers=await auth(client, "agente2"))
    assert r.status_code == 403 and r.json()["code"] == "ocorrencia.nao_e_autor"

    r = await client.put(
        f"/v1/ocorrencias/{oid}",
        json={"descricao": "Descrição complementada com placa ABC-1234.", "latitude": -29.70, "envolvidos": [{"nome": "Ana", "tipo": "TESTEMUNHA"}]},
        headers=ha,
    )
    assert r.status_code == 200, r.text
    assert r.json()["latitude"] == -29.70 and r.json()["envolvidos"][0]["nome"] == "Ana"

    r = await client.post(f"/v1/ocorrencias/{oid}/reenviar", headers=ha)
    assert r.status_code == 200 and r.json()["status"] == "AGUARDANDO_REVISAO"
    r = await client.post(f"/v1/ocorrencias/{oid}/validar", headers=hd)
    assert r.status_code == 200
    assert [h["para"] for h in r.json()["historico_status"]] == ["AGUARDANDO_REVISAO", "EM_CORRECAO", "AGUARDANDO_REVISAO", "VALIDADA"]
    assert r.json()["narrativa_integra"] is True


async def test_editar_fora_de_correcao_422(client):
    ha = await auth(client, "agente")
    o = await registrar(client, ha)
    r = await client.put(f"/v1/ocorrencias/{o['ocorrencia_id']}", json={"natureza": "Roubo"}, headers=ha)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.invalid_transition"


async def test_rejeitar_terminal(client):
    o = await registrar(client, await auth(client, "agente"))
    hd = await auth(client, "delegado")
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/rejeitar", json={"justificativa": "Fato atípico, sem materialidade."}, headers=hd)
    assert r.status_code == 200 and r.json()["status"] == "REJEITADA"
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/reenviar", headers=await auth(client, "agente"))
    assert r.status_code == 422


async def test_auditoria_consultavel_pelo_delegado(client):
    o = await registrar(client, await auth(client, "agente"))
    hd = await auth(client, "delegado")
    await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=hd)
    r = await client.get("/v1/auditoria", params={"entidade_id": o["ocorrencia_id"]}, headers=hd)
    assert r.status_code == 200
    assert [x["operacao"] for x in r.json()] == ["ocorrencia.validar", "ocorrencia.registrar"]
    r = await client.get("/v1/auditoria", headers=await auth(client, "agente"))
    assert r.status_code == 403
