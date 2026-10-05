"""Integração HTTP + persistência: Medidas Protetivas (RF09 / UC09 / sq09)."""
from uuid import uuid4

from tests.integration.helpers import auth, registrar


async def test_fluxo_medidas_protetivas(client):
    h_agente = await auth(client, "agente")
    h_delegado = await auth(client, "delegado")

    # 1. Registra ocorrência com envolvidos
    oc = await registrar(client, h_agente, envolvidos=[{"nome": "Maria", "tipo": "VITIMA", "email": "vitima@email.com"}])
    oc_id = oc["ocorrencia_id"]
    detalhe = (await client.get(f"/v1/ocorrencias/{oc_id}", headers=h_agente)).json()
    vitima_id = detalhe["envolvidos"][0]["id"]
    agressor_id = str(uuid4())

    # 2. Agente tenta conceder medida -> 403
    r_negado = await client.post(
        "/v1/medidas-protetivas",
        json={
            "ocorrencia_id": oc_id,
            "vitima_id": vitima_id,
            "agressor_id": agressor_id,
            "tipos_restricao": ["AFASTAMENTO_DO_LAR", "PROIBICAO_DE_CONTATO"],
            "prazo_dias": 90,
            "distancia_minima_metros": 300,
        },
        headers=h_agente,
    )
    assert r_negado.status_code == 403

    # 3. Delegado concede medida protetiva
    r_conc = await client.post(
        "/v1/medidas-protetivas",
        json={
            "ocorrencia_id": oc_id,
            "vitima_id": vitima_id,
            "agressor_id": agressor_id,
            "tipos_restricao": ["AFASTAMENTO_DO_LAR", "PROIBICAO_DE_CONTATO"],
            "prazo_dias": 90,
            "distancia_minima_metros": 300,
        },
        headers=h_delegado,
    )
    assert r_conc.status_code == 201, r_conc.text
    medida = r_conc.json()
    assert medida["numero_referencia"].startswith("MP-")
    assert medida["status"] == "ATIVA"
    assert medida["prazo_dias"] == 90
    assert medida["dias_restantes"] == 90
    medida_id = medida["id"]

    # 4. Listar medidas
    r_list = await client.get("/v1/medidas-protetivas", headers=h_agente)
    assert r_list.status_code == 200
    assert r_list.json()["total"] >= 1

    # 5. Delegado renova medida protetiva
    r_ren = await client.post(
        f"/v1/medidas-protetivas/{medida_id}/renovar",
        json={
            "dias_adicionais": 30,
            "justificativa": "Persistência do risco de reiteração delitiva do agressor.",
        },
        headers=h_delegado,
    )
    assert r_ren.status_code == 200, r_ren.text
    assert r_ren.json()["status"] == "RENOVADA"
    assert r_ren.json()["prazo_dias"] == 120

    # 6. Testar envio individual de alerta de vencimento por e-mail
    r_alerta_ind = await client.post(
        f"/v1/medidas-protetivas/{medida_id}/enviar-alerta-vencimento",
        json={"email_destinatario": "vitima@email.com"},
        headers=h_delegado,
    )
    assert r_alerta_ind.status_code == 200, r_alerta_ind.text
    res_ind = r_alerta_ind.json()
    assert res_ind["sucesso"] is True
    assert res_ind["modo"] == "manual"
    assert res_ind["alertas_enviados"] == 1

    # 7. Testar verificação em lote de vencimentos
    r_verificar = await client.post(
        "/v1/medidas-protetivas/verificar-vencimentos",
        headers=h_delegado,
    )
    assert r_verificar.status_code == 200
    res_batch = r_verificar.json()
    assert res_batch["sucesso"] is True
    assert res_batch["modo"] == "automatico_lote"
    assert "total_processadas" in res_batch

    # 8. Delegado revoga medida protetiva
    r_rev = await client.post(
        f"/v1/medidas-protetivas/{medida_id}/revogar",
        json={"motivo": "Decisão judicial extinguindo as cautelares concedidas."},
        headers=h_delegado,
    )
    assert r_rev.status_code == 200, r_rev.text
    assert r_rev.json()["status"] == "REVOGADA"

