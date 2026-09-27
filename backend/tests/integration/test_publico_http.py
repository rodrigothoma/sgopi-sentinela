"""Integração HTTP: portal público de autenticação de documentos — /v1/publico/documentos (RF08 / UC08)."""
from uuid import UUID

from sqlalchemy import select, update

from infrastructure.database.models import OcorrenciaModel, RegistroAuditoriaModel
from tests.integration.helpers import auth, registrar

ROTA = "/v1/publico/documentos"


async def _documento_emitido(client, **overrides) -> dict:
    """Registra como agente, valida como delegado e devolve o detalhe (com chave e hash)."""
    o = await registrar(client, await auth(client, "agente"), **overrides)
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=await auth(client, "delegado"))
    assert r.status_code == 200, r.text
    return r.json()


async def test_validacao_emite_chave_visivel_no_detalhe(client):
    doc = await _documento_emitido(client)
    assert doc["chave_autenticidade"] and len(doc["chave_autenticidade"]) == 24
    assert doc["hash_narrativa"] and len(doc["hash_narrativa"]) == 64


async def test_ocorrencia_nao_validada_nao_tem_chave(client):
    o = await registrar(client, await auth(client, "agente"))
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}", headers=await auth(client, "agente"))
    assert r.json()["chave_autenticidade"] is None


async def test_autenticar_por_chave_sem_login_documento_autentico(client, session):
    doc = await _documento_emitido(client, envolvidos=[{"nome": "Maria Souza", "tipo": "VITIMA", "documento": "123.456.789-09"}])
    chave = doc["chave_autenticidade"]
    formatada = "-".join(chave[i : i + 4] for i in range(0, 24, 4)).lower()

    r = await client.get(f"{ROTA}/{formatada}", headers={"X-Forwarded-For": "198.51.100.9"})
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["situacao"] == "AUTENTICO"
    assert corpo["numero_protocolo"] == doc["numero_protocolo"]
    assert corpo["chave_autenticidade"] == chave and corpo["chave_formatada"] == formatada.upper()
    assert corpo["hash_integridade"] == doc["hash_narrativa"]
    assert corpo["status_ocorrencia"] == "VALIDADA" and corpo["emitido_em"]
    assert corpo["envolvidos_por_tipo"] == {"VITIMA": 1}
    assert corpo["tipificacoes"] == [{"artigo": "Art. 155 CP", "descricao": "Furto simples"}]
    # LGPD / RNF02: nada que identifique pessoas nem a narrativa
    assert "Maria" not in r.text and "789" not in r.text and "localizacao" not in corpo and "descricao" not in corpo

    stmt = select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "documento.autenticar")
    registro = (await session.execute(stmt)).scalar_one()
    assert registro.quem is None and registro.ip == "198.51.100.9"
    assert registro.entidade_id == doc["ocorrencia_id"] and registro.dados_depois["situacao"] == "AUTENTICO"


async def test_autenticar_pelo_hash_sha256(client):
    doc = await _documento_emitido(client)
    r = await client.get(f"{ROTA}/{doc['hash_narrativa']}")
    assert r.status_code == 200 and r.json()["situacao"] == "AUTENTICO"
    assert r.json()["numero_protocolo"] == doc["numero_protocolo"]


async def test_chave_desconhecida_404_nao_reconhecido_e_auditada(client, session):
    r = await client.get(f"{ROTA}/ZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZ")
    assert r.status_code == 404 and r.json()["code"] == "documento.not_found"
    stmt = select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "documento.nao_localizado")
    registro = (await session.execute(stmt)).scalar_one()
    assert registro.quem is None and registro.dados_depois["codigo_sufixo"] == "ZZZZ"


async def test_codigo_mal_formado_422(client):
    r = await client.get(f"{ROTA}/ABCD-ABCD-ABCD-ABCD-ABCD-ABC0")
    assert r.status_code == 422 and r.json()["code"] == "documento.codigo_invalido"
    r = await client.get(f"{ROTA}/curta")
    assert r.status_code == 422 and r.json()["code"] == "generic.validation_error"


async def test_narrativa_adulterada_no_banco_documento_adulterado_com_alerta(client, session):
    doc = await _documento_emitido(client)
    await session.execute(
        update(OcorrenciaModel)
        .where(OcorrenciaModel.id == UUID(doc["ocorrencia_id"]))
        .values(descricao="Texto alterado diretamente na base, fora do fluxo do sistema.")
    )
    await session.commit()

    r = await client.get(f"{ROTA}/{doc['chave_autenticidade']}")
    assert r.status_code == 200 and r.json()["situacao"] == "ADULTERADO"
    stmt = select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "documento.suspeita_fraude")
    assert (await session.execute(stmt)).scalar_one().entidade_id == doc["ocorrencia_id"]


async def test_documento_de_ocorrencia_excluida_indisponivel(client):
    doc = await _documento_emitido(client)
    r = await client.post(
        f"/v1/ocorrencias/{doc['ocorrencia_id']}/excluir",
        json={"motivo": "Registro anulado por decisão judicial."},
        headers=await auth(client, "delegado"),
    )
    assert r.status_code == 200, r.text
    r = await client.get(f"{ROTA}/{doc['chave_autenticidade']}")
    assert r.status_code == 200 and r.json()["situacao"] == "INDISPONIVEL"


async def test_chaves_sao_unicas_entre_documentos(client):
    a = await _documento_emitido(client)
    b = await _documento_emitido(client)
    assert a["chave_autenticidade"] != b["chave_autenticidade"]
    r = await client.get(f"{ROTA}/{b['chave_autenticidade']}")
    assert r.json()["numero_protocolo"] == b["numero_protocolo"]
