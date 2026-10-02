"""Testes de integração: Registro e Consulta Pública de Ocorrência (/v1/ocorrencias/publico)."""
from datetime import UTC, datetime, timedelta
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from infrastructure.database.models import OcorrenciaModel


@pytest.fixture
def corpo_publico():
    return {
        "nome_solicitante": "Carlos Alberto da Silva",
        "documento": "52998224725",  # CPF com checksum válido
        "email": "carlos.silva@exemplo.com",
        "telefone": "(55) 99876-5432",
        "declaracao_maioridade": True,
        "natureza": "Furto",
        "descricao": "Bicicleta aro 29 furtada no bicicletário da praça central por volta do meio-dia.",
        "localizacao": "Praça Getúlio Vargas, Centro, Alegrete - RS",
        "latitude": -29.7833,
        "longitude": -55.7917,
        "data_hora_fato": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
    }


async def test_registro_publico_sucesso_narrativa_pura_e_comunicante(client, session, usuarios):
    """Garante narrativa limpa, qualificação como COMUNICANTE e gravação de e-mail e telefone."""
    payload = {
        "nome_solicitante": "Carlos Alberto da Silva",
        "documento": "52998224725",
        "email": "carlos.silva@exemplo.com",
        "telefone": "(55) 99876-5432",
        "declaracao_maioridade": True,
        "natureza": "Furto",
        "descricao": "Bicicleta aro 29 furtada no bicicletário da praça central por volta do meio-dia.",
        "localizacao": "Praça Getúlio Vargas, Centro, Alegrete - RS",
        "latitude": -29.7833,
        "longitude": -55.7917,
        "data_hora_fato": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
    }
    r = await client.post("/v1/ocorrencias/publico", json=payload)
    assert r.status_code == 201, r.text
    dados = r.json()
    assert "SGOPI-" in dados["numero_protocolo"]
    assert dados["status"] == "AGUARDANDO_REVISAO"

    # Verifica no banco de dados
    stmt = (
        select(OcorrenciaModel)
        .where(OcorrenciaModel.id == uuid.UUID(dados["ocorrencia_id"]))
        .options(selectinload(OcorrenciaModel.envolvidos))
    )
    model = (await session.execute(stmt)).scalar_one()

    # Narrativa pura sem gambiarras textuais
    assert "[REGISTRO CIDADÃO VIA WEB]" not in model.descricao
    assert model.descricao == payload["descricao"]

    # Comunicante qualificado
    assert len(model.envolvidos) == 1
    comunicante = model.envolvidos[0]
    assert comunicante.tipo == "COMUNICANTE"
    assert comunicante.nome == "Carlos Alberto da Silva"
    assert comunicante.documento == "52998224725"
    assert comunicante.email == "carlos.silva@exemplo.com"
    assert comunicante.telefone == "(55) 99876-5432"


async def test_registro_publico_rejeita_cpf_invalido_422(client, corpo_publico):
    corpo_publico["documento"] = "111.111.111-11"  # Repetido e inválido
    r = await client.post("/v1/ocorrencias/publico", json=corpo_publico)
    assert r.status_code == 422
    assert "CPF informado é inválido" in r.text


async def test_registro_publico_rejeita_sem_maioridade_422(client, corpo_publico):
    corpo_publico["declaracao_maioridade"] = False
    r = await client.post("/v1/ocorrencias/publico", json=corpo_publico)
    assert r.status_code == 422
    assert "declaração de maioridade" in r.text


async def test_consulta_publica_por_protocolo(client, corpo_publico):
    r_reg = await client.post("/v1/ocorrencias/publico", json=corpo_publico)
    assert r_reg.status_code == 201
    protocolo = r_reg.json()["numero_protocolo"]

    r_cons = await client.get(f"/v1/ocorrencias/publico/{protocolo}")
    assert r_cons.status_code == 200
    dados = r_cons.json()
    assert dados["numero_protocolo"] == protocolo
    assert dados["natureza"] == "Furto"
    assert dados["status"] == "AGUARDANDO_REVISAO"


async def test_consulta_publica_nao_expoe_desfecho_nem_dados_pessoais(client, corpo_publico):
    protocolo = (await client.post("/v1/ocorrencias/publico", json=corpo_publico)).json()["numero_protocolo"]
    dados = (await client.get(f"/v1/ocorrencias/publico/{protocolo}")).json()
    assert set(dados) == {"numero_protocolo", "status", "natureza", "localizacao", "criada_em"}


async def test_consulta_publica_aceita_protocolo_em_minusculas(client, corpo_publico):
    protocolo = (await client.post("/v1/ocorrencias/publico", json=corpo_publico)).json()["numero_protocolo"]
    r = await client.get(f"/v1/ocorrencias/publico/{protocolo.lower()}")
    assert r.status_code == 200 and r.json()["numero_protocolo"] == protocolo


async def test_consulta_publica_protocolo_inexistente_404_com_mensagem_propria(client):
    r = await client.get("/v1/ocorrencias/publico/SGOPI-2026-999999")
    assert r.status_code == 404
    assert r.json()["code"] == "ocorrencia.protocolo_nao_encontrado"
    assert "protocolo informado" in r.json()["detail"]


async def test_consulta_publica_trata_excluida_como_inexistente(client, corpo_publico):
    from tests.integration.helpers import auth

    reg = (await client.post("/v1/ocorrencias/publico", json=corpo_publico)).json()
    r = await client.post(
        f"/v1/ocorrencias/{reg['ocorrencia_id']}/excluir",
        json={"motivo": "Registro de teste em duplicidade."},
        headers=await auth(client, "delegado"),
    )
    assert r.status_code == 200, r.text
    r = await client.get(f"/v1/ocorrencias/publico/{reg['numero_protocolo']}")
    assert r.status_code == 404


async def test_registro_publico_exige_declaracao_explicita(client, corpo_publico):
    del corpo_publico["declaracao_maioridade"]
    r = await client.post("/v1/ocorrencias/publico", json=corpo_publico)
    assert r.status_code == 422


async def test_registro_publico_limitado_por_ip_429(client, corpo_publico):
    """A fixture limita a 5 comunicações por IP; a 6ª é recusada com Retry-After."""
    for _ in range(4):
        assert (await client.post("/v1/ocorrencias/publico", json=corpo_publico)).status_code == 201
    r = await client.post("/v1/ocorrencias/publico", json=corpo_publico)
    assert r.status_code == 201  # 5ª atinge a cota
    r = await client.post("/v1/ocorrencias/publico", json=corpo_publico)
    assert r.status_code == 429
    assert r.json()["code"] == "generic.muitas_tentativas"
    assert int(r.headers["Retry-After"]) > 0


async def test_x_forwarded_for_de_cliente_nao_confiavel_e_ignorado(app, corpo_publico):
    """IP forjado em X-Forwarded-For não burla a cota quando a conexão não vem de proxy confiável."""
    from httpx import ASGITransport, AsyncClient

    transporte = ASGITransport(app=app, raise_app_exceptions=False, client=("203.0.113.7", 5000))
    async with AsyncClient(transport=transporte, base_url="http://test") as c:
        status = [
            (await c.post("/v1/ocorrencias/publico", json=corpo_publico, headers={"X-Forwarded-For": f"10.0.0.{i}"})).status_code
            for i in range(6)
        ]
    assert status[-1] == 429
