"""E2E de API: caminhos de erro (401/403/404/409/422) contra o backend real."""
from uuid import uuid4

import httpx

from tests.e2e.conftest import corpo_ocorrencia


def test_sem_token_devolve_401(client: httpx.Client):
    assert client.get("/v1/ocorrencias").status_code == 401
    assert client.get("/v1/viaturas").status_code == 401


def test_token_invalido_401(client: httpx.Client):
    r = client.get("/v1/ocorrencias", headers={"Authorization": "Bearer token.falso.x"})
    assert r.status_code == 401


def test_agente_nao_pode_validar_403(client: httpx.Client, auth, ocorrencia_registrada):
    r = client.post(f"/v1/ocorrencias/{ocorrencia_registrada['ocorrencia_id']}/validar", headers=auth("agente"))
    assert r.status_code == 403


def test_operador_nao_registra_ocorrencia_403(client: httpx.Client, auth):
    r = client.post("/v1/ocorrencias", json=corpo_ocorrencia(), headers=auth("operador"))
    assert r.status_code == 403


def test_ocorrencia_inexistente_404(client: httpx.Client, auth):
    assert client.get(f"/v1/ocorrencias/{uuid4()}", headers=auth("delegado")).status_code == 404


def test_descricao_curta_422_com_chave_i18n(client: httpx.Client, auth):
    r = client.post("/v1/ocorrencias", json=corpo_ocorrencia(descricao="curta"), headers=auth("agente"))
    assert r.status_code == 422
    assert r.json()["code"] == "ocorrencia.descricao_curta"


def test_segunda_validacao_conflita(client: httpx.Client, auth, ocorrencia_registrada):
    oc_id = ocorrencia_registrada["ocorrencia_id"]
    assert client.post(f"/v1/ocorrencias/{oc_id}/validar", headers=auth("delegado")).status_code == 200
    # segunda validação: transição inválida (422)
    r = client.post(f"/v1/ocorrencias/{oc_id}/validar", headers=auth("delegado"))
    assert r.status_code == 422


def test_paginacao_limit_offset(client: httpx.Client, auth):
    r = client.get("/v1/ocorrencias?limit=1&offset=0", headers=auth("delegado"))
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["limit"] == 1 and corpo["offset"] == 0
    assert len(corpo["itens"]) <= 1
    assert "total" in corpo
