"""Integração HTTP + persistência: Inquéritos Policiais (RF06 / UC06 / sq06)."""
from uuid import uuid4

from tests.integration.helpers import auth, registrar


async def test_fluxo_completo_inquerito(client):
    h_agente = await auth(client, "agente")
    h_delegado = await auth(client, "delegado")

    # 1. Agente registra uma ocorrência
    oc = await registrar(client, h_agente)
    oc_id = oc["ocorrencia_id"]

    # Delegado valida a ocorrência
    r_val = await client.post(f"/v1/ocorrencias/{oc_id}/validar", json={"justificativa": "Validada conforme apuração preliminar"}, headers=h_delegado)
    assert r_val.status_code == 200, r_val.text

    # 2. Agente tenta instaurar inquérito -> 403
    r_inst_negado = await client.post(
        "/v1/inqueritos",
        json={"ementa": "Tentativa indevida de instauração", "ocorrencias_iniciais_ids": [oc_id]},
        headers=h_agente,
    )
    assert r_inst_negado.status_code == 403

    # 3. Delegado instaura inquérito com a ocorrência validada
    r_inst = await client.post(
        "/v1/inqueritos",
        json={
            "ementa": "Apuração detalhada de furto qualificado continuado",
            "ocorrencias_iniciais_ids": [oc_id],
        },
        headers=h_delegado,
    )
    assert r_inst.status_code == 201, r_inst.text
    inq = r_inst.json()
    assert inq["numero"].startswith("IP-")
    assert inq["status"] == "EM_ANDAMENTO"
    assert len(inq["ocorrencias"]) == 1
    assert inq["ocorrencias"][0]["id"] == oc_id
    inq_id = inq["id"]

    # 4. Consulta / listagem de inquéritos
    r_list = await client.get("/v1/inqueritos", headers=h_delegado)
    assert r_list.status_code == 200
    dados_list = r_list.json()
    assert dados_list["total"] >= 1
    assert any(i["id"] == inq_id for i in dados_list["itens"])

    # 5. Detalhe do inquérito
    r_det = await client.get(f"/v1/inqueritos/{inq_id}", headers=h_delegado)
    assert r_det.status_code == 200
    assert r_det.json()["id"] == inq_id

    # 6. Concluir inquérito
    r_conc = await client.post(
        f"/v1/inqueritos/{inq_id}/concluir",
        json={"relatorio_final": "Relatório final conclusivo com identificação e autoria delimitadas."},
        headers=h_delegado,
    )
    assert r_conc.status_code == 200
    assert r_conc.json()["status"] == "CONCLUIDO"
    assert r_conc.json()["concluido_em"] is not None


async def test_sugestao_conexoes(client):
    h_agente = await auth(client, "agente")
    h_delegado = await auth(client, "delegado")

    # Registra ocorrência 1
    oc1 = await registrar(client, h_agente)
    oc1_id = oc1["ocorrencia_id"]
    await client.post(f"/v1/ocorrencias/{oc1_id}/validar", json={"justificativa": "Validada 1"}, headers=h_delegado)

    # Busca conexões
    r_conexoes = await client.get(f"/v1/inqueritos/conexoes/{oc1_id}", headers=h_delegado)
    assert r_conexoes.status_code == 200
    assert isinstance(r_conexoes.json(), list)
