"""Integração HTTP: arquivar/excluir com autorização do Delegado + motivo (RF20)."""
from datetime import UTC, datetime

from uuid import UUID

from sqlalchemy import select

from infrastructure.database.models import OcorrenciaModel, RegistroAuditoriaModel
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, registrar

MOTIVO = {"motivo": "Registro em duplicidade com o protocolo anterior."}


async def test_arquivar_exige_delegado_e_motivo(client, session):
    ha, hd = await auth(client, "agente"), await auth(client, "delegado")
    o = await registrar(client, ha)
    oid = o["ocorrencia_id"]

    r = await client.post(f"/v1/ocorrencias/{oid}/arquivar", json=MOTIVO, headers=ha)
    assert r.status_code == 403
    r = await client.post(f"/v1/ocorrencias/{oid}/arquivar", json=MOTIVO, headers=await auth(client, "operador"))
    assert r.status_code == 403
    r = await client.post(f"/v1/ocorrencias/{oid}/arquivar", json={"motivo": "curto"}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.motivo_curto"
    r = await client.post(f"/v1/ocorrencias/{oid}/arquivar", json={}, headers=hd)
    assert r.status_code == 422

    r = await client.post(f"/v1/ocorrencias/{oid}/arquivar", json=MOTIVO, headers=hd)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["status"] == "ARQUIVADA" and corpo["arquivada_por_id"] == str(IDS["delegado"])
    assert corpo["motivo_arquivamento"] == MOTIVO["motivo"]
    assert corpo["historico_status"][-1]["para"] == "ARQUIVADA" and corpo["historico_status"][-1]["justificativa"] == MOTIVO["motivo"]

    aud = (await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "ocorrencia.arquivar"))).scalars().all()
    assert len(aud) == 1 and aud[0].quem == IDS["delegado"] and aud[0].dados_depois["justificativa"] == MOTIVO["motivo"]

    # o agente autor continua vendo a ocorrência (arquivada) na própria lista
    r = await client.get("/v1/ocorrencias", headers=ha)
    assert [i["status"] for i in r.json()["itens"]] == ["ARQUIVADA"]
    # arquivada não é editável nem revisável
    r = await client.post(f"/v1/ocorrencias/{oid}/validar", headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.invalid_transition"


async def test_excluir_e_logico_some_da_listagem_e_fica_auditavel(client, session):
    ha, hd = await auth(client, "agente"), await auth(client, "delegado")
    o = await registrar(client, ha)
    outra = await registrar(client, ha)
    oid = o["ocorrencia_id"]

    r = await client.post(f"/v1/ocorrencias/{oid}/excluir", json=MOTIVO, headers=ha)
    assert r.status_code == 403
    r = await client.post(f"/v1/ocorrencias/{oid}/excluir", json=MOTIVO, headers=hd)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "EXCLUIDA" and r.json()["excluida_por_id"] == str(IDS["delegado"])
    assert r.json()["motivo_exclusao"] == MOTIVO["motivo"]

    # listagem sem filtro oculta; filtro explícito mostra; detalhe segue consultável
    r = await client.get("/v1/ocorrencias", headers=hd)
    assert [i["ocorrencia_id"] for i in r.json()["itens"]] == [outra["ocorrencia_id"]] and r.json()["total"] == 1
    r = await client.get("/v1/ocorrencias", params={"status": "EXCLUIDA"}, headers=hd)
    assert [i["ocorrencia_id"] for i in r.json()["itens"]] == [oid]
    r = await client.get(f"/v1/ocorrencias/{oid}", headers=hd)
    assert r.status_code == 200 and r.json()["status"] == "EXCLUIDA"

    # nada foi apagado fisicamente (RNF03*)
    model = await session.get(OcorrenciaModel, UUID(oid))
    assert model is not None and model.status == "EXCLUIDA" and model.motivo_exclusao == MOTIVO["motivo"]

    # terminal
    r = await client.post(f"/v1/ocorrencias/{oid}/arquivar", json=MOTIVO, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.invalid_transition"
    r = await client.post(f"/v1/ocorrencias/{oid}/excluir", json=MOTIVO, headers=hd)
    assert r.status_code == 422


async def test_nao_arquiva_nem_exclui_em_atendimento(client):
    ha, hd, ho = await auth(client, "agente"), await auth(client, "delegado"), await auth(client, "operador")
    o = await registrar(client, ha)
    oid = o["ocorrencia_id"]
    await client.post(f"/v1/ocorrencias/{oid}/validar", headers=hd)
    v = (await client.post("/v1/viaturas", json={"prefixo": "VTR-09", "placa": "P090000"}, headers=ho)).json()
    await client.post("/v1/telemetria/posicoes", json={"viatura_id": v["id"], "latitude": -29.78, "longitude": -55.79, "registrada_em": datetime.now(UTC).isoformat()}, headers=ho)
    r = await client.post("/v1/despachos", json={"ocorrencia_id": oid, "viatura_id": v["id"]}, headers=ho)
    assert r.status_code == 201, r.text

    for acao in ("arquivar", "excluir"):
        r = await client.post(f"/v1/ocorrencias/{oid}/{acao}", json=MOTIVO, headers=hd)
        assert r.status_code == 422 and r.json()["extra"]["status_atual"] == "EM_ATENDIMENTO"
