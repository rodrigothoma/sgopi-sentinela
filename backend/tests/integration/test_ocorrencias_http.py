"""Integração HTTP: POST /v1/ocorrencias (RF01* critérios de aceite)."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from infrastructure.database.models import EvidenciaModel, OcorrenciaModel, RegistroAuditoriaModel
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, corpo_ocorrencia, registrar


async def test_registrar_ocorrencia_201_protocolo_e_status_inicial(client, session):
    out = await registrar(client, await auth(client, "agente"))
    assert out["numero_protocolo"] == f"SGOPI-{datetime.now(UTC).year}-000001"
    assert out["status"] == "AGUARDANDO_REVISAO"
    model = await session.get(OcorrenciaModel, __import__("uuid").UUID(out["ocorrencia_id"]))
    assert model.agente_policial_id == IDS["agente"]  # critério 5: vem do token
    assert model.latitude == -29.7833
    aud = (await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "ocorrencia.registrar"))).scalars().all()
    assert len(aud) == 1 and aud[0].entidade_id == out["ocorrencia_id"]


async def test_agente_policial_id_no_body_e_ignorado(client, session):
    out = await registrar(client, await auth(client, "agente"), agente_policial_id=str(IDS["delegado"]))
    model = await session.get(OcorrenciaModel, __import__("uuid").UUID(out["ocorrencia_id"]))
    assert model.agente_policial_id == IDS["agente"]


async def test_sem_envolvido_422_i18n(client):
    h = await auth(client, "agente")
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(envolvidos=[]), headers=h)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.sem_envolvidos"
    assert r.json()["detail"] == "É obrigatória a qualificação de ao menos um envolvido"
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(envolvidos=[]), headers={**h, "Accept-Language": "en"})
    assert r.json()["detail"] == "At least one involved person is required"


async def test_coordenada_fora_da_faixa_422(client):
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(latitude=91), headers=await auth(client, "agente"))
    assert r.status_code == 422 and r.json()["code"] == "geo.latitude_fora_da_faixa"


async def test_data_fato_futura_422(client):
    futuro = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(data_hora_fato=futuro), headers=await auth(client, "agente"))
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.data_fato_futura"


async def test_cpf_invalido_422(client):
    r = await client.post(
        "/v1/ocorrencias",
        json=corpo_ocorrencia(envolvidos=[{"nome": "X", "tipo": "SUSPEITO", "documento": "123.456.789-00"}]),
        headers=await auth(client, "agente"),
    )
    assert r.status_code == 422 and r.json()["code"] == "envolvido.cpf_invalido"


async def test_descricao_curta_422_com_extra(client):
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(descricao="curta"), headers=await auth(client, "agente"))
    assert r.status_code == 422 and r.json()["extra"] == {"minimo": 20}


async def test_body_malformado_422_padronizado(client):
    r = await client.post("/v1/ocorrencias", json={"natureza": "x"}, headers=await auth(client, "agente"))
    assert r.status_code == 422 and r.json()["code"] == "generic.validation_error"


async def test_protocolos_sao_sequenciais(client):
    h = await auth(client, "agente")
    p = [(await registrar(client, h))["numero_protocolo"] for _ in range(3)]
    assert [x[-6:] for x in p] == ["000001", "000002", "000003"]


async def test_anexar_evidencia_persiste_e_aparece_no_detalhe(app, client, session, tmp_path):
    from adapters.outbound.arquivos.armazenamento_disco import ArmazenamentoDisco
    from infrastructure.di import get_armazenamento_arquivos

    app.dependency_overrides[get_armazenamento_arquivos] = lambda: ArmazenamentoDisco(tmp_path)
    h = await auth(client, "agente")
    ocorrencia = await registrar(client, h)
    conteudo = b"%PDF-1.7\nevidencia"
    r = await client.post(
        f"/v1/ocorrencias/{ocorrencia['ocorrencia_id']}/evidencias",
        files={"arquivo": ("laudo.pdf", conteudo, "application/pdf")},
        headers=h,
    )
    assert r.status_code == 201, r.text
    evidencia = r.json()
    assert evidencia["nome_original"] == "laudo.pdf" and evidencia["tamanho"] == len(conteudo)
    model = (await session.execute(select(EvidenciaModel))).scalar_one()
    assert str(model.ocorrencia_id) == ocorrencia["ocorrencia_id"]
    assert (tmp_path / model.chave_armazenamento).read_bytes() == conteudo
    detalhe = (await client.get(f"/v1/ocorrencias/{ocorrencia['ocorrencia_id']}", headers=h)).json()
    assert detalhe["evidencias"][0]["hash_sha256"] == evidencia["hash_sha256"]


async def test_anexar_evidencia_rejeita_formato_e_ocorrencia_inexistente(client):
    h = await auth(client, "agente")
    r = await client.post(
        f"/v1/ocorrencias/{__import__('uuid').uuid4()}/evidencias",
        files={"arquivo": ("x.pdf", b"%PDF-1.7", "application/pdf")},
        headers=h,
    )
    assert r.status_code == 404 and r.json()["code"] == "ocorrencia.not_found"
    ocorrencia = await registrar(client, h)
    r = await client.post(
        f"/v1/ocorrencias/{ocorrencia['ocorrencia_id']}/evidencias",
        files={"arquivo": ("script.exe", b"MZ", "application/octet-stream")},
        headers=h,
    )
    assert r.status_code == 422 and r.json()["code"] == "evidencia.formato_invalido"
