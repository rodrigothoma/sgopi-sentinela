"""Integração HTTP das sugestões #1 (busca), #2 (aviso ao agente autor) e #3 (exportação CSV)."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from adapters.inbound.http.exportacao_csv import BOM_UTF8
from infrastructure.database.models import RegistroAuditoriaModel
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, registrar


# ------------------------------------------------------------- #1 busca
async def test_busca_por_natureza_texto_protocolo_e_periodo(client):
    ha = await auth(client, "agente")
    furto = await registrar(client, ha, natureza="Furto", data_hora_fato=(datetime.now(UTC) - timedelta(days=10)).isoformat())
    roubo = await registrar(client, ha, natureza="Roubo", descricao="Roubo de celular 100% novo_em_folha na praça.")
    hd = await auth(client, "delegado")

    async def ids(**params):
        r = await client.get("/v1/ocorrencias", params=params, headers=hd)
        assert r.status_code == 200, r.text
        return [i["ocorrencia_id"] for i in r.json()["itens"]]

    assert await ids(natureza="roUBO") == [roubo["ocorrencia_id"]]
    assert await ids(protocolo=furto["numero_protocolo"].lower()) == [furto["ocorrencia_id"]]
    assert await ids(texto="100% novo_em") == [roubo["ocorrencia_id"]]
    assert await ids(texto="1000%") == []  # curingas do usuário são literais
    assert await ids(texto="alegrete") == [furto["ocorrencia_id"], roubo["ocorrencia_id"]]  # localização
    corte = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    assert await ids(data_fato_de=corte) == [roubo["ocorrencia_id"]]
    assert await ids(data_fato_ate=corte) == [furto["ocorrencia_id"]]
    assert await ids(origem="PUBLICA") == []


async def test_busca_valida_periodo_e_origem(client):
    hd = await auth(client, "delegado")
    agora = datetime.now(UTC)
    r = await client.get(
        "/v1/ocorrencias", params={"data_fato_de": agora.isoformat(), "data_fato_ate": (agora - timedelta(days=1)).isoformat()}, headers=hd
    )
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.periodo_invalido"
    r = await client.get("/v1/ocorrencias", params={"origem": "XPTO"}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.origem_invalida"


# ---------------------------------------------------- #2 aviso ao autor
async def test_devolucao_notifica_somente_o_agente_autor(client):
    o = await registrar(client, await auth(client, "agente"))
    hd = await auth(client, "delegado")
    r = await client.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/devolver", json={"justificativa": "Faltam dados do veículo."}, headers=hd)
    assert r.status_code == 200, r.text

    r = await client.get("/v1/notificacoes", headers=await auth(client, "agente"))
    [n] = [i for i in r.json()["itens"] if i["tipo"] == "REVISAO_OCORRENCIA"]
    assert o["numero_protocolo"] in n["titulo"] and "Faltam dados do veículo." in n["mensagem"]
    assert n["link"] == f"/minhas?protocolo={o['numero_protocolo']}&ocorrencia={o['ocorrencia_id']}" and n["usuario_id"] == str(IDS["agente"])
    r = await client.get("/v1/notificacoes", headers=await auth(client, "agente2"))
    assert not [i for i in r.json()["itens"] if i["tipo"] == "REVISAO_OCORRENCIA"]


# ------------------------------------------------------- #3 exportação
async def test_exportacao_de_ocorrencias_em_csv_e_auditada(client, session):
    ha = await auth(client, "agente")
    await registrar(client, ha, natureza="Furto")
    await registrar(client, ha, natureza="Roubo")
    r = await client.get("/v1/ocorrencias/exportar", params={"natureza": "furto"}, headers=await auth(client, "supervisor"))
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"].startswith('attachment; filename="ocorrencias_')
    linhas = r.text.removeprefix(BOM_UTF8).strip().split("\r\n")
    assert linhas[0].startswith("numero_protocolo;natureza;status") and len(linhas) == 2 and ";Furto;" in linhas[1]

    registro = (
        await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "ocorrencias.exportar"))
    ).scalar_one()
    assert registro.quem == IDS["supervisor"]
    assert registro.dados_depois["total_linhas"] == 1 and registro.dados_depois["filtros"]["natureza"] == "furto"


async def test_exportacao_de_auditoria_mascara_cpf_e_e_auditada(client, session):
    await registrar(client, await auth(client, "agente"), envolvidos=[{"nome": "X", "tipo": "VITIMA", "documento": "123.456.789-09"}])
    r = await client.get("/v1/auditoria/exportar", params={"formato": "csv", "entidade": "Ocorrencia"}, headers=await auth(client, "delegado"))
    assert r.status_code == 200, r.text
    assert r.text.startswith(BOM_UTF8) and "123.456.789-09" not in r.text and "12345678909" not in r.text
    assert r.text.removeprefix(BOM_UTF8).startswith("quando;operacao;entidade")
    operacoes = (await session.execute(select(RegistroAuditoriaModel.operacao))).scalars().all()
    assert "auditoria.exportar" in operacoes


async def test_exportacao_restrita_a_delegado_e_supervisor(client):
    for login in ("agente", "operador"):
        h = await auth(client, login)
        assert (await client.get("/v1/ocorrencias/exportar", headers=h)).status_code == 403
        assert (await client.get("/v1/auditoria/exportar", headers=h)).status_code == 403
    assert (await client.get("/v1/ocorrencias/exportar")).status_code == 401
    r = await client.get("/v1/auditoria/exportar", params={"formato": "xlsx"}, headers=await auth(client, "delegado"))
    assert r.status_code == 422
