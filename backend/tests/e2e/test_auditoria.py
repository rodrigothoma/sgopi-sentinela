"""E2E: trilha de auditoria (RNF03) registra o fluxo de uma ocorrência."""
import httpx


def test_auditoria_registra_fluxo_e_agente_nao_consulta(client: httpx.Client, auth, ocorrencia_registrada):
    oc_id = ocorrencia_registrada["ocorrencia_id"]
    assert client.post(f"/v1/ocorrencias/{oc_id}/validar", headers=auth("delegado")).status_code == 200

    # Delegado consulta a trilha
    r = client.get("/v1/auditoria", params={"entidade": "Ocorrencia", "entidade_id": oc_id}, headers=auth("delegado"))
    assert r.status_code == 200, r.text
    operacoes = [reg["operacao"] for reg in r.json()]
    assert "ocorrencia.registrar" in operacoes
    assert "ocorrencia.validar" in operacoes

    # Agente não pode consultar a auditoria (RNF02 / RNF03: só Delegado/Supervisor)
    assert client.get("/v1/auditoria", headers=auth("agente")).status_code == 403
