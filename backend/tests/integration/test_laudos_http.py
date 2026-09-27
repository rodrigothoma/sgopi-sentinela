"""Integração HTTP + persistência: Laudos Periciais (RF07 / UC07 / sq07)."""
from tests.integration.helpers import auth, registrar


async def test_fluxo_laudo_pericial(client):
    h_agente = await auth(client, "agente")
    h_delegado = await auth(client, "delegado")
    h_perito = await auth(client, "perito")

    # 1. Registra ocorrência
    oc = await registrar(client, h_agente)
    oc_id = oc["ocorrencia_id"]

    # 2. Agente tenta solicitar laudo -> 403
    r_negado = await client.post(
        "/v1/laudos",
        json={
            "tipo_pericia": "BALISTICA",
            "descricao_solicitacao": "Exame de confronto balístico em estojos e projéteis",
            "ocorrencia_id": oc_id,
        },
        headers=h_agente,
    )
    assert r_negado.status_code == 403

    # 3. Delegado solicita laudo pericial
    r_sol = await client.post(
        "/v1/laudos",
        json={
            "tipo_pericia": "BALISTICA",
            "descricao_solicitacao": "Exame de confronto balístico em estojos e projéteis",
            "ocorrencia_id": oc_id,
        },
        headers=h_delegado,
    )
    assert r_sol.status_code == 201, r_sol.text
    laudo = r_sol.json()
    assert laudo["numero_referencia"].startswith("LP-")
    assert laudo["status"] == "SOLICITADO"
    assert laudo["tipo_pericia"] == "BALISTICA"
    laudo_id = laudo["id"]

    # 4. Listagem de laudos
    r_list = await client.get("/v1/laudos", headers=h_perito)
    assert r_list.status_code == 200
    assert r_list.json()["total"] >= 1

    # 5. Perito anexa conclusão com upload multipart de arquivo PDF
    pdf_bytes = b"%PDF-1.4 Laudo pericial com conclusoes tecnicas e parecer balistico."
    files = {"arquivo": ("laudo_balistica.pdf", pdf_bytes, "application/pdf")}
    data = {"conclusoes_tecnicas": "Confronto microscópico balístico positivo com estriamento idêntico."}

    r_anexar = await client.post(
        f"/v1/laudos/{laudo_id}/anexar",
        data=data,
        files=files,
        headers=h_perito,
    )
    assert r_anexar.status_code == 200, r_anexar.text
    laudo_concluido = r_anexar.json()
    assert laudo_concluido["status"] == "CONCLUIDO"
    assert laudo_concluido["hash_sha256"] is not None
    assert len(laudo_concluido["hash_sha256"]) == 64

    # 6. Obter laudo
    r_det = await client.get(f"/v1/laudos/{laudo_id}", headers=h_delegado)
    assert r_det.status_code == 200
    assert r_det.json()["id"] == laudo_id
    assert r_det.json()["status"] == "CONCLUIDO"
