"""Integração HTTP + persistência: inventário de apreensões e Auto de Apreensão (RF03 / UC03)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import OcorrenciaRepositorioSQLAlchemy
from adapters.outbound.persistence.unidade_de_trabalho_sqlalchemy import UnidadeDeTrabalhoSQLAlchemy
from domain.ocorrencia.apreensao import EstadoConservacao, ItemApreendido, TipoItemApreendido, UnidadeMedida
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.geo import Coordenada
from infrastructure.database.models import ItemApreendidoModel, MovimentacaoCustodiaModel, RegistroAuditoriaModel
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, corpo_ocorrencia, registrar

AGORA = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def corpo_item(**overrides) -> dict:
    corpo = {
        "tipo": "OBJETO",
        "descricao": "Aparelho celular Samsung preto",
        "quantidade": 1,
        "estado_conservacao": "BOM",
        "numero_lacre": "LACRE-0001",
        "localizacao_deposito": "Cofre 2 — prateleira A",
    }
    corpo.update(overrides)
    return corpo


async def registrar_item(client, headers, ocorrencia_id, **overrides) -> dict:
    r = await client.post(f"/v1/ocorrencias/{ocorrencia_id}/apreensoes", json=corpo_item(**overrides), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ------------------------------------------------------------------ registrar

async def test_registrar_item_201_persiste_e_aparece_no_detalhe(client, session):
    h = await auth(client, "agente")
    o = await registrar(client, h)
    item = await registrar_item(client, h, o["ocorrencia_id"], numero_lacre=" lacre-0001 ")
    assert item["numero_lacre"] == "LACRE-0001" and item["localizacao_atual"] == "Cofre 2 — prateleira A"
    assert str(IDS["agente"]) == item["registrado_por_id"] and item["movimentacoes"][0]["origem"] is None

    model = (await session.execute(select(ItemApreendidoModel))).scalar_one()
    assert str(model.ocorrencia_id) == o["ocorrencia_id"] and model.numero_lacre == "LACRE-0001"
    movs = (await session.execute(select(MovimentacaoCustodiaModel))).scalars().all()
    assert len(movs) == 1 and movs[0].ordem == 0 and movs[0].destino == "Cofre 2 — prateleira A"
    aud = (await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "apreensao.registrar"))).scalar_one()
    assert aud.entidade_id == item["id"]

    detalhe = (await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}", headers=h)).json()
    assert detalhe["itens_apreendidos"][0]["id"] == item["id"] and detalhe["versao"] == 2


async def test_arma_de_fogo_exige_calibre_e_marca_422(client):
    h = await auth(client, "agente")
    o = await registrar(client, h)
    r = await client.post(
        f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes",
        json=corpo_item(tipo="ARMA_DE_FOGO", descricao="Revólver", marca="Taurus"),
        headers=h,
    )
    assert r.status_code == 422 and r.json()["code"] == "apreensao.arma_sem_calibre_ou_marca"
    assert r.json()["detail"] == "Arma de fogo exige calibre e marca"
    await registrar_item(client, h, o["ocorrencia_id"], tipo="ARMA_DE_FOGO", descricao="Revólver", marca="Taurus", calibre=".38")


async def test_lacre_duplicado_em_outra_ocorrencia_409(client):
    h = await auth(client, "agente")
    o1 = await registrar(client, h)
    o2 = await registrar(client, h)
    await registrar_item(client, h, o1["ocorrencia_id"], numero_lacre="L-1")
    r = await client.post(f"/v1/ocorrencias/{o2['ocorrencia_id']}/apreensoes", json=corpo_item(numero_lacre="l-1"), headers=h)
    assert r.status_code == 409 and r.json()["code"] == "apreensao.lacre_duplicado"
    assert r.json()["extra"] == {"numero_lacre": "L-1"}


async def test_validacoes_de_schema_e_papel(client):
    h = await auth(client, "agente")
    o = await registrar(client, h)
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes", json=corpo_item(quantidade=0), headers=h)
    assert r.status_code == 422 and r.json()["code"] == "generic.validation_error"
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes", json=corpo_item(tipo="BICICLETA"), headers=h)
    assert r.status_code == 422 and r.json()["code"] == "apreensao.tipo_invalido"
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes", json=corpo_item(), headers=await auth(client, "delegado"))
    assert r.status_code == 403
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes", json=corpo_item(), headers=await auth(client, "agente2"))
    assert r.status_code == 403 and r.json()["code"] == "ocorrencia.nao_e_autor"
    r = await client.post(f"/v1/ocorrencias/{uuid4()}/apreensoes", json=corpo_item(), headers=h)
    assert r.status_code == 404 and r.json()["code"] == "ocorrencia.not_found"


# ----------------------------------------------------------------- custódia

async def test_movimentar_custodia_append_only(client, session):
    h = await auth(client, "agente")
    o = await registrar(client, h)
    item = await registrar_item(client, h, o["ocorrencia_id"])
    hd = await auth(client, "delegado")
    r = await client.post(
        f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes/{item['id']}/movimentacoes",
        json={"destino": "Depósito central — caixa 7", "observacao": "para perícia"},
        headers=hd,
    )
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["localizacao_atual"] == "Depósito central — caixa 7" and out["localizacao_deposito"] == "Cofre 2 — prateleira A"
    assert [m["destino"] for m in out["movimentacoes"]] == ["Cofre 2 — prateleira A", "Depósito central — caixa 7"]
    assert out["movimentacoes"][1]["por_id"] == str(IDS["delegado"]) and out["movimentacoes"][1]["origem"] == "Cofre 2 — prateleira A"

    movs = (await session.execute(select(MovimentacaoCustodiaModel).order_by(MovimentacaoCustodiaModel.ordem))).scalars().all()
    assert [m.ordem for m in movs] == [0, 1]

    # mesmo destino → 422; item inexistente → 404; operador → 403
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes/{item['id']}/movimentacoes", json={"destino": "Depósito central — caixa 7"}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "apreensao.destino_igual_origem"
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes/{uuid4()}/movimentacoes", json={"destino": "X"}, headers=hd)
    assert r.status_code == 404 and r.json()["code"] == "apreensao.not_found"
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/apreensoes/{item['id']}/movimentacoes", json={"destino": "X"}, headers=await auth(client, "operador"))
    assert r.status_code == 403


# -------------------------------------------------------------- auto de apreensão

async def test_auto_de_apreensao_emitido_com_hash_e_auditoria(client, session):
    h = await auth(client, "agente")
    o = await registrar(client, h)
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}/auto-apreensao", headers=h)
    assert r.status_code == 422 and r.json()["code"] == "apreensao.sem_itens"

    await registrar_item(client, h, o["ocorrencia_id"], numero_lacre="L-1")
    await registrar_item(client, h, o["ocorrencia_id"], numero_lacre="L-2", tipo="ENTORPECENTE", quantidade=250, unidade="GRAMA", descricao="Substância análoga à maconha")
    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}/auto-apreensao", headers=await auth(client, "delegado"))
    assert r.status_code == 200, r.text
    auto = r.json()
    assert auto["numero"] == f"AA-{o['numero_protocolo']}" and auto["numero_protocolo"] == o["numero_protocolo"]
    assert [i["numero_lacre"] for i in auto["itens"]] == ["L-1", "L-2"] and len(auto["hash_sha256"]) == 64
    assert auto["emitido_por_id"] == str(IDS["delegado"]) and auto["agente_policial_id"] == str(IDS["agente"])
    aud = (await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "apreensao.emitir_auto"))).scalar_one()
    assert aud.entidade_id == auto["numero"] and aud.dados_depois["hash_sha256"] == auto["hash_sha256"]

    r = await client.get(f"/v1/ocorrencias/{o['ocorrencia_id']}/auto-apreensao", headers=await auth(client, "agente2"))
    assert r.status_code == 403 and r.json()["code"] == "ocorrencia.nao_e_autor"


# ------------------------------------------------------ repositório round-trip

async def test_repositorio_round_trip_itens_e_cadeia_de_custodia(session, usuarios):
    repo, uow = OcorrenciaRepositorioSQLAlchemy(session), UnidadeDeTrabalhoSQLAlchemy(session)
    o = Ocorrencia.registrar(
        agente_policial_id=usuarios["agente"],
        natureza="Tráfico",
        descricao="Apreensão de entorpecentes em abordagem de rotina.",
        localizacao="Av. Brasil, 500",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[Envolvido(nome="Carlos", tipo=TipoEnvolvido.SUSPEITO)],
    )
    item = ItemApreendido(
        tipo=TipoItemApreendido.ARMA_DE_FOGO,
        descricao="Pistola",
        quantidade=1,
        unidade=UnidadeMedida.UNIDADE,
        estado_conservacao=EstadoConservacao.REGULAR,
        numero_lacre="L-9",
        numero_serie="XYZ",
        marca="Taurus",
        calibre="9mm",
        localizacao_deposito="Cofre 1",
        registrado_em=AGORA,
        registrado_por_id=usuarios["agente"],
    )
    o.registrar_apreensao(item, usuarios["agente"], AGORA)
    async with uow:
        await repo.salvar(o)
        await uow.commit()
    assert await repo.lacre_em_uso("L-9") and not await repo.lacre_em_uso("L-10")

    lida = await repo.buscar_por_id(o.id)
    lida.movimentar_item_apreendido(item.id, usuarios["delegado"], "Perícia", "laudo", AGORA + timedelta(hours=1))
    async with uow:
        await repo.salvar(lida)
        await uow.commit()

    relida = await repo.buscar_por_id(o.id)
    i = relida.itens_apreendidos[0]
    assert (i.tipo, i.marca, i.calibre, i.numero_serie, i.estado_conservacao) == (TipoItemApreendido.ARMA_DE_FOGO, "Taurus", "9mm", "XYZ", EstadoConservacao.REGULAR)
    assert i.registrado_em == AGORA and i.registrado_em.tzinfo is not None
    assert [(m.origem, m.destino) for m in i.movimentacoes] == [(None, "Cofre 1"), ("Cofre 1", "Perícia")]
    assert i.movimentacoes[1].por_id == usuarios["delegado"] and i.localizacao_atual == "Perícia"
    assert relida.versao == 3


# --------------------------------------- registro concomitante via POST /v1/ocorrencias

async def test_registrar_ocorrencia_com_itens_apreendidos_opcionais(client, session):
    h = await auth(client, "agente")
    sem_itens = await registrar(client, h)  # campo ausente → compatível com o contrato anterior
    detalhe = (await client.get(f"/v1/ocorrencias/{sem_itens['ocorrencia_id']}", headers=h)).json()
    assert detalhe["itens_apreendidos"] == []

    com_itens = await registrar(
        client, h,
        itens_apreendidos=[corpo_item(numero_lacre="L-1"), corpo_item(numero_lacre="L-2", tipo="ENTORPECENTE", quantidade=50, unidade="GRAMA", descricao="Cocaína")],
    )
    detalhe = (await client.get(f"/v1/ocorrencias/{com_itens['ocorrencia_id']}", headers=h)).json()
    assert [i["numero_lacre"] for i in detalhe["itens_apreendidos"]] == ["L-1", "L-2"] and detalhe["versao"] == 1
    assert detalhe["itens_apreendidos"][1]["registrado_por_id"] == str(IDS["agente"])
    ops = (await session.execute(select(RegistroAuditoriaModel.operacao).where(RegistroAuditoriaModel.operacao.like("apreensao.%")))).scalars().all()
    assert ops == ["apreensao.registrar", "apreensao.registrar"]

    # auto já pode ser emitido a partir do registro
    r = await client.get(f"/v1/ocorrencias/{com_itens['ocorrencia_id']}/auto-apreensao", headers=h)
    assert r.status_code == 200 and len(r.json()["itens"]) == 2


async def test_registrar_ocorrencia_com_item_invalido_e_atomico(client, session):
    h = await auth(client, "agente")
    antes = (await client.get("/v1/ocorrencias", headers=h)).json()["total"]
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(itens_apreendidos=[corpo_item(tipo="ARMA_DE_FOGO", descricao="Revólver")]), headers=h)
    assert r.status_code == 422 and r.json()["code"] == "apreensao.arma_sem_calibre_ou_marca"
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(itens_apreendidos=[corpo_item(quantidade=0)]), headers=h)
    assert r.status_code == 422 and r.json()["code"] == "generic.validation_error"
    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(itens_apreendidos=[corpo_item(numero_lacre="X-1"), corpo_item(numero_lacre="x-1")]), headers=h)
    assert r.status_code == 409 and r.json()["code"] == "apreensao.lacre_duplicado"
    assert (await client.get("/v1/ocorrencias", headers=h)).json()["total"] == antes
    assert (await session.execute(select(ItemApreendidoModel))).scalars().all() == []
