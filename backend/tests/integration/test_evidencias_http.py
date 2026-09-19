"""Integração HTTP da conferência e download seguro de evidências."""
from uuid import uuid4

import pytest
from sqlalchemy import select

from adapters.outbound.arquivos.armazenamento_disco import ArmazenamentoDisco
from infrastructure.database.models import EvidenciaModel
from infrastructure.di import get_armazenamento_arquivos
from tests.integration.helpers import auth, registrar

CONTEUDO = b"%PDF-1.7\nevidencia para download"


@pytest.fixture
async def evidencia_http(app, client, session, tmp_path):
    armazenamento = ArmazenamentoDisco(tmp_path)
    app.dependency_overrides[get_armazenamento_arquivos] = lambda: armazenamento
    headers = await auth(client, "agente")
    ocorrencia = await registrar(client, headers)
    resposta = await client.post(
        f"/v1/ocorrencias/{ocorrencia['ocorrencia_id']}/evidencias",
        files={"arquivo": ("laudo técnico.pdf", CONTEUDO, "application/pdf")},
        headers=headers,
    )
    assert resposta.status_code == 201, resposta.text
    model = (await session.execute(select(EvidenciaModel))).scalar_one()
    return ocorrencia, resposta.json(), model, headers, tmp_path


def url(ocorrencia: dict, evidencia: dict, sufixo: str) -> str:
    return f"/v1/ocorrencias/{ocorrencia['ocorrencia_id']}/evidencias/{evidencia['id']}/{sufixo}"


async def test_integridade_integra_e_sem_expor_chave(client, evidencia_http):
    ocorrencia, evidencia, model, headers, tmp_path = evidencia_http
    resposta = await client.get(url(ocorrencia, evidencia, "integridade"), headers=headers)
    assert resposta.status_code == 200
    assert resposta.json() == {"evidencia_id": evidencia["id"], "estado": "INTEGRA"}
    serializado = resposta.text + str(resposta.headers)
    assert model.chave_armazenamento not in serializado and str(tmp_path) not in serializado


async def test_integridade_divergente(client, evidencia_http):
    ocorrencia, evidencia, model, headers, tmp_path = evidencia_http
    (tmp_path / model.chave_armazenamento).write_bytes(b"adulterado")
    resposta = await client.get(url(ocorrencia, evidencia, "integridade"), headers=headers)
    assert resposta.status_code == 200 and resposta.json()["estado"] == "DIVERGENTE"


async def test_download_conteudo_headers_e_sem_caminho(client, evidencia_http):
    ocorrencia, evidencia, model, headers, tmp_path = evidencia_http
    resposta = await client.get(url(ocorrencia, evidencia, "download"), headers=headers)
    assert resposta.status_code == 200 and resposta.content == CONTEUDO
    assert resposta.headers["content-type"] == "application/pdf"
    assert resposta.headers["content-disposition"] == "attachment; filename*=UTF-8''laudo%20t%C3%A9cnico.pdf"
    assert resposta.headers["x-content-type-options"] == "nosniff"
    assert model.chave_armazenamento not in str(resposta.headers)
    assert str(tmp_path) not in str(resposta.headers)


async def test_rotas_exigem_autenticacao(client, evidencia_http):
    ocorrencia, evidencia, *_ = evidencia_http
    for sufixo in ("integridade", "download"):
        assert (await client.get(url(ocorrencia, evidencia, sufixo))).status_code == 401


async def test_agente_nao_autor_recebe_403(client, evidencia_http):
    ocorrencia, evidencia, *_ = evidencia_http
    resposta = await client.get(
        url(ocorrencia, evidencia, "download"), headers=await auth(client, "agente2")
    )
    assert resposta.status_code == 403


async def test_integridade_agente_nao_autor_recebe_403(client, evidencia_http):
    ocorrencia, evidencia, *_ = evidencia_http
    resposta = await client.get(
        url(ocorrencia, evidencia, "integridade"), headers=await auth(client, "agente2")
    )
    assert resposta.status_code == 403


async def test_ocorrencia_e_evidencia_inexistentes_404(client, evidencia_http):
    ocorrencia, evidencia, _, headers, _ = evidencia_http
    inexistente = str(uuid4())
    resposta_ocorrencia = await client.get(
        f"/v1/ocorrencias/{inexistente}/evidencias/{evidencia['id']}/integridade",
        headers=headers,
    )
    resposta_evidencia = await client.get(
        f"/v1/ocorrencias/{ocorrencia['ocorrencia_id']}/evidencias/{inexistente}/integridade",
        headers=headers,
    )
    assert resposta_ocorrencia.status_code == 404
    assert resposta_evidencia.status_code == 404


async def test_arquivo_fisico_ausente_recebe_404(client, evidencia_http):
    ocorrencia, evidencia, model, headers, tmp_path = evidencia_http
    (tmp_path / model.chave_armazenamento).unlink()
    resposta = await client.get(url(ocorrencia, evidencia, "integridade"), headers=headers)
    assert resposta.status_code == 404
    assert resposta.json()["code"] == "evidencia.arquivo_ausente"


async def test_download_divergente_bloqueado(client, evidencia_http):
    ocorrencia, evidencia, model, headers, tmp_path = evidencia_http
    (tmp_path / model.chave_armazenamento).write_bytes(b"adulterado")
    resposta = await client.get(url(ocorrencia, evidencia, "download"), headers=headers)
    assert resposta.status_code == 409
    assert resposta.json()["code"] == "evidencia.integridade_divergente"
