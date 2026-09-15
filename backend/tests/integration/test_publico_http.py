"""Integração HTTP do portal público de autenticação de documento (RF08 / UC08) — sem token."""
from sqlalchemy import select, update

from infrastructure.database.models import OcorrenciaModel, RegistroAuditoriaModel
from tests.integration.helpers import auth, registrar


async def _emitir(client) -> dict:
    o = await registrar(client, await auth(client, "agente"), envolvidos=[{"nome": "Maria", "tipo": "VITIMA", "documento": "123.456.789-09"}])
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=await auth(client, "delegado"))
    assert r.status_code == 200, r.text
    return r.json()


async def test_detalhe_expoe_chave_somente_apos_validacao(client):
    ha = await auth(client, "agente")
    o = await registrar(client, ha)
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}", headers=ha)
    assert r.json()["chave_autenticidade"] is None

    detalhe = await _emitir(client)
    chave = detalhe["chave_autenticidade"]
    assert chave and len(chave) == 29 and chave.count("-") == 5  # XXXX-XXXX-XXXX-XXXX-XXXX-XXXX


async def test_portal_publico_autentica_sem_token_e_sem_dados_pessoais(client, session):
    detalhe = await _emitir(client)
    r = await client.get(f"/v1/publico/documentos/{detalhe['chave_autenticidade']}")
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["numero_protocolo"] == detalhe["numero_protocolo"]
    assert corpo["situacao"] == "VALIDO" and corpo["status_ocorrencia"] == "VALIDADA"
    assert corpo["hash_integridade"] == detalhe["hash_narrativa"]
    assert corpo["envolvidos_por_tipo"] == {"VITIMA": 1}
    assert corpo["tipificacoes"] == [{"artigo": "Art. 155 CP", "descricao": "Furto simples"}]
    for campo in ("envolvidos", "descricao", "localizacao", "latitude", "agente_policial_id"):
        assert campo not in corpo
    assert "Maria" not in r.text and "123.456.789-09" not in r.text

    ops = (await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "documento.consulta_publica"))).scalars().all()
    assert len(ops) == 1 and ops[0].quem is None and ops[0].entidade_id == detalhe["ocorrencia_id"]


async def test_chave_pode_ser_digitada_sem_hifens_e_em_minusculas(client):
    detalhe = await _emitir(client)
    r = await client.get(f"/v1/publico/documentos/{detalhe['chave_autenticidade'].replace('-', '').lower()}")
    assert r.status_code == 200 and r.json()["situacao"] == "VALIDO"


async def test_documento_adulterado_no_banco_e_denunciado(client, session):
    detalhe = await _emitir(client)
    await session.execute(
        update(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == detalhe["numero_protocolo"]).values(descricao="Narrativa reescrita por fora do sistema.")
    )
    await session.commit()

    r = await client.get(f"/v1/publico/documentos/{detalhe['chave_autenticidade']}")
    assert r.status_code == 200 and r.json()["situacao"] == "ADULTERADO"
    ops = (await session.execute(select(RegistroAuditoriaModel.operacao))).scalars().all()
    assert "documento.suspeita_fraude" in ops


async def test_chave_inexistente_404_e_malformada_422(client):
    r = await client.get("/v1/publico/documentos/ABCDEFGHJKLMNPQRSTUVWXYZ")
    assert r.status_code == 404 and r.json()["code"] == "documento.not_found"
    r = await client.get("/v1/publico/documentos/ABCD-ABCD-ABCD-ABCD-ABCD-AB0O")
    assert r.status_code == 422 and r.json()["code"] == "documento.chave_invalida"
    r = await client.get("/v1/publico/documentos/curta")
    assert r.status_code == 422


async def test_mensagem_de_erro_respeita_accept_language(client):
    r = await client.get("/v1/publico/documentos/ABCDEFGHJKLMNPQRSTUVWXYZ", headers={"Accept-Language": "en"})
    assert r.status_code == 404 and r.json()["detail"].startswith("Document not found")
