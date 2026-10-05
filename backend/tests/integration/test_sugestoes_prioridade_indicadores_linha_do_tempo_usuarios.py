"""Integração HTTP das sugestões #7 (prioridade), #11 (indicadores), #12 (linha do tempo) e #13 (usuários)."""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from adapters.outbound.arquivos.armazenamento_disco import ArmazenamentoDisco
from infrastructure.database.models import OcorrenciaModel, RegistroAuditoriaModel, UsuarioModel
from infrastructure.di import get_armazenamento_arquivos
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, registrar
from tests.integration.test_apreensoes_http import corpo_item

JUSTIFICATIVA = "Há relato de arma de fogo no local."


async def _viatura(client, ho, prefixo="VTR-01") -> str:
    v = (await client.post("/v1/viaturas", json={"prefixo": prefixo, "placa": f"P{prefixo[-2:]}0000"}, headers=ho)).json()
    await client.post(
        "/v1/telemetria/posicoes",
        json={"viatura_id": v["id"], "latitude": -29.7833, "longitude": -55.7919, "registrada_em": datetime.now(UTC).isoformat()},
        headers=ho,
    )
    return v["id"]


# ------------------------------------------------------------ #7 prioridade
async def test_prioridade_sugerida_ajustada_ordenada_e_redefinida(client, session):
    ha = await auth(client, "agente")
    furto = await registrar(client, ha, natureza="Furto")
    roubo = await registrar(client, ha, natureza="Roubo")
    urgente = await registrar(client, ha, natureza="Furto", prioridade="URGENTE")
    assert (furto["prioridade"], roubo["prioridade"], urgente["prioridade"]) == ("MEDIA", "ALTA", "URGENTE")
    hd = await auth(client, "delegado")

    r = await client.get("/v1/ocorrencias", params={"status": "AGUARDANDO_REVISAO", "ordenar_por_prioridade": "true"}, headers=hd)
    assert [i["ocorrencia_id"] for i in r.json()["itens"]] == [urgente["ocorrencia_id"], roubo["ocorrencia_id"], furto["ocorrencia_id"]]
    assert r.json()["itens"][0]["prioridade"] == "URGENTE"

    url = f"/v1/ocorrencias/{furto['ocorrencia_id']}/prioridade"
    assert (await client.post(url, json={"prioridade": "ALTA", "justificativa": JUSTIFICATIVA}, headers=ha)).status_code == 403
    r = await client.post(url, json={"prioridade": "XPTO", "justificativa": JUSTIFICATIVA}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "ocorrencia.prioridade_invalida"
    r = await client.post(url, json={"prioridade": "URGENTE", "justificativa": JUSTIFICATIVA}, headers=hd)
    assert r.status_code == 200 and r.json()["prioridade"] == "URGENTE"
    aud = (
        await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "ocorrencia.redefinir_prioridade"))
    ).scalar_one()
    assert aud.dados_antes["prioridade"] == "MEDIA" and aud.dados_depois["justificativa"] == JUSTIFICATIVA
    model = await session.get(OcorrenciaModel, UUID(furto["ocorrencia_id"]))
    await session.refresh(model)
    assert model.prioridade == "URGENTE"


async def test_registro_rejeita_prioridade_invalida(client):
    r = await client.post("/v1/ocorrencias", json={"prioridade": "MAXIMA"}, headers=await auth(client, "agente"))
    assert r.status_code == 422


# --------------------------------------------------------- #12 linha do tempo
async def test_linha_do_tempo_reune_fontes_em_ordem(app, client, tmp_path):
    app.dependency_overrides[get_armazenamento_arquivos] = lambda: ArmazenamentoDisco(tmp_path)
    ha, hd, ho = await auth(client, "agente"), await auth(client, "delegado"), await auth(client, "operador")
    o = await registrar(client, ha)
    oid = o["ocorrencia_id"]
    r = await client.post(f"/v1/ocorrencias/{oid}/apreensoes", json=corpo_item(), headers=ha)
    assert r.status_code == 201, r.text
    ev = (await client.post(f"/v1/ocorrencias/{oid}/evidencias", files={"arquivo": ("foto.pdf", b"%PDF-1.7 x", "application/pdf")}, headers=ha)).json()
    assert (await client.get(f"/v1/ocorrencias/{oid}/evidencias/{ev['id']}/integridade", headers=hd)).status_code == 200
    assert (await client.post(f"/v1/ocorrencias/{oid}/validar", headers=hd)).status_code == 200
    viatura = await _viatura(client, ho)
    assert (await client.post("/v1/despachos", json={"ocorrencia_id": oid, "viatura_id": viatura}, headers=ho)).status_code == 201
    assert (await client.post(f"/v1/ocorrencias/{oid}/encerrar", json={"desfecho": "Atendimento concluído sem intercorrências."}, headers=ho)).status_code == 200

    r = await client.get(f"/v1/ocorrencias/{oid}/linha-do-tempo", headers=hd)
    assert r.status_code == 200, r.text
    eventos = r.json()
    tipos = [e["tipo"] for e in eventos]
    for tipo in ("STATUS", "ITEM_APREENDIDO", "CUSTODIA_MOVIMENTADA", "EVIDENCIA_ANEXADA", "INTEGRIDADE_VERIFICADA", "DESPACHO", "ORDEM_ENCERRADA"):
        assert tipo in tipos, tipo
    assert [e["em"] for e in eventos] == sorted(e["em"] for e in eventos)
    status = [e["detalhes"]["para"] for e in eventos if e["tipo"] == "STATUS"]
    assert status == ["AGUARDANDO_REVISAO", "VALIDADA", "EM_ATENDIMENTO", "ENCERRADA"]
    despacho = next(e for e in eventos if e["tipo"] == "DESPACHO")
    assert despacho["detalhes"]["viatura"] == "VTR-01" and despacho["por_id"] == str(IDS["operador"]) and despacho["por_nome"]
    integridade = next(e for e in eventos if e["tipo"] == "INTEGRIDADE_VERIFICADA")
    assert integridade["detalhes"]["integridade"] == "INTEGRA"

    assert (await client.get(f"/v1/ocorrencias/{oid}/linha-do-tempo", headers=await auth(client, "agente2"))).status_code == 403
    assert (await client.get(f"/v1/ocorrencias/{oid}/linha-do-tempo", headers=ha)).status_code == 200


# --------------------------------------------------------- #11 indicadores
async def test_indicadores_agregados_no_banco(client):
    ha, hd, ho = await auth(client, "agente"), await auth(client, "delegado"), await auth(client, "operador")
    validada = await registrar(client, ha, natureza="Furto")
    devolvida = await registrar(client, ha, natureza="Furto")
    await registrar(client, ha, natureza="Roubo")
    await client.post(f"/v1/ocorrencias/{validada['ocorrencia_id']}/validar", headers=hd)
    await client.post(f"/v1/ocorrencias/{devolvida['ocorrencia_id']}/devolver", json={"justificativa": "Faltam dados do veículo."}, headers=hd)
    viatura = await _viatura(client, ho)
    await client.post("/v1/despachos", json={"ocorrencia_id": validada["ocorrencia_id"], "viatura_id": viatura}, headers=ho)
    await client.post(f"/v1/ocorrencias/{validada['ocorrencia_id']}/encerrar", json={"desfecho": "Atendimento concluído sem intercorrências."}, headers=ho)

    r = await client.get("/v1/indicadores", params={"fuso": "America/Sao_Paulo"}, headers=hd)
    assert r.status_code == 200, r.text
    k = r.json()
    assert k["total_ocorrencias"] == 3
    assert {c["chave"]: c["total"] for c in k["por_natureza"]} == {"Furto": 2, "Roubo": 1}
    assert {c["chave"]: c["total"] for c in k["por_origem"]} == {"POLICIAL": 3}
    assert sum(k["por_faixa_horaria"]) == 3 and len(k["por_faixa_horaria"]) == 24
    assert {c["chave"]: c["total"] for c in k["decisoes"]} == {"VALIDADA": 1, "EM_CORRECAO": 1, "REJEITADA": 0}
    assert k["taxa_devolucao"] == 0.5 and k["taxa_rejeicao"] == 0.0
    for chave in ("tempo_ate_decisao", "tempo_validacao_despacho", "tempo_despacho_encerramento"):
        assert k[chave]["amostras"] >= 1 and k[chave]["media_segundos"] >= 0, chave
    assert k["tempo_ate_decisao"]["amostras"] == 2
    assert sum(k["despachos_por_hora"]) == 1
    assert {c["chave"]: c["total"] for c in k["viaturas_por_situacao"]} == {"DISPONIVEL": 1}

    assert (await client.get("/v1/indicadores", headers=ho)).status_code == 200
    assert (await client.get("/v1/indicadores", headers=ha)).status_code == 403
    r = await client.get("/v1/indicadores", params={"fuso": "Marte/Olympus"}, headers=hd)
    assert r.status_code == 422 and r.json()["code"] == "indicadores.fuso_invalido"


# ------------------------------------------------------------ #13 usuários
async def test_gestao_de_usuarios_ponta_a_ponta(client, session):
    hs = await auth(client, "supervisor")
    corpo = {"nome": "Carlos Lima", "login": "Carlos.Lima", "senha": "NovaSenha1", "papel": "AGENTE"}
    assert (await client.post("/v1/usuarios", json=corpo, headers=await auth(client, "delegado"))).status_code == 403
    r = await client.post("/v1/usuarios", json=corpo, headers=hs)
    assert r.status_code == 201, r.text
    novo = r.json()
    assert novo["login"] == "carlos.lima" and novo["ativo"] is True
    assert (await client.post("/v1/usuarios", json=corpo, headers=hs)).status_code == 409

    login = await client.post("/v1/auth/login", json={"login": "carlos.lima", "senha": "NovaSenha1"})
    assert login.status_code == 200
    h_novo = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get("/v1/ocorrencias", headers=h_novo)).status_code == 200

    # troca de papel derruba a sessão antiga (o token ainda diz AGENTE)
    r = await client.patch(f"/v1/usuarios/{novo['id']}/papel", json={"papel": "PERITO"}, headers=hs)
    assert r.status_code == 200 and r.json()["papel"] == "PERITO"
    assert (await client.get("/v1/ocorrencias", headers=h_novo)).status_code == 401

    # desativar é lógico: some do efetivo, não entra mais, mas a linha continua no banco
    assert (await client.post(f"/v1/usuarios/{novo['id']}/desativar", json={"motivo": "Transferido"}, headers=hs)).json()["ativo"] is False
    assert (await client.post("/v1/auth/login", json={"login": "carlos.lima", "senha": "NovaSenha1"})).status_code == 401
    assert novo["id"] not in [u["id"] for u in (await client.get("/v1/usuarios", headers=hs)).json()]
    gestao = {u["id"]: u for u in (await client.get("/v1/usuarios/gestao", headers=hs)).json()}
    assert gestao[novo["id"]]["ativo"] is False
    assert (await session.execute(select(UsuarioModel).where(UsuarioModel.login == "carlos.lima"))).scalar_one() is not None

    assert (await client.post(f"/v1/usuarios/{novo['id']}/reativar", headers=hs)).json()["ativo"] is True
    assert (await client.post("/v1/auth/login", json={"login": "carlos.lima", "senha": "NovaSenha1"})).status_code == 200

    r = await client.post(f"/v1/usuarios/{IDS['supervisor']}/desativar", headers=hs)
    assert r.status_code == 403 and r.json()["code"] == "usuario.proprio"
    operacoes = (await session.execute(select(RegistroAuditoriaModel.operacao).where(RegistroAuditoriaModel.entidade == "Usuario"))).scalars().all()
    for op in ("usuario.cadastrar", "usuario.alterar_papel", "usuario.desativar", "usuario.reativar"):
        assert op in operacoes
    assert (await client.get("/v1/usuarios/gestao", headers=await auth(client, "delegado"))).status_code == 403
