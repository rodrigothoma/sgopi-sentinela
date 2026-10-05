"""
Integração HTTP: Trilha de Auditoria Imutável e Logs Sanitizados (RNF02 / RNF03).

Critérios de Aceite:
1. RBAC estrito: apenas DELEGADO e SUPERVISOR podem consultar a auditoria.
2. AGENTE recebe 403 Forbidden; requisições sem token recebem 401 Unauthorized.
3. Imutabilidade (RNF03): métodos mutativos (POST, PUT, PATCH, DELETE) retornam 405 Method Not Allowed.
4. Filtros por entidade, operacao, quem e entidade_id funcionam com precisão.
5. Proteção de dados (RNF02): CPFs em payloads dados_antes / dados_depois são mascarados recursivamente.
"""
from datetime import UTC, datetime
from uuid import uuid4

from infrastructure.database.models import RegistroAuditoriaModel
from tests.integration.conftest import IDS
from tests.integration.helpers import auth, registrar


async def test_delegado_e_supervisor_podem_consultar_auditoria(client):
    # Delegado
    r_del = await client.get("/v1/auditoria", headers=await auth(client, "delegado"))
    assert r_del.status_code == 200
    assert isinstance(r_del.json(), list)

    # Supervisor
    r_sup = await client.get("/v1/auditoria", headers=await auth(client, "supervisor"))
    assert r_sup.status_code == 200
    assert isinstance(r_sup.json(), list)


async def test_agente_e_anonimo_recebem_403_e_401(client):
    # Agente: 403 Forbidden
    r_ag = await client.get("/v1/auditoria", headers=await auth(client, "agente"))
    assert r_ag.status_code == 403
    assert r_ag.json()["code"] == "auth.forbidden"
    assert "DELEGADO" in r_ag.json()["extra"]["exigido"]
    assert "SUPERVISOR" in r_ag.json()["extra"]["exigido"]

    # Anônimo: 401 Unauthorized
    r_anon = await client.get("/v1/auditoria")
    assert r_anon.status_code == 401


async def test_imutabilidade_metodos_mutativos_rejeitados_405(client):
    headers = await auth(client, "delegado")
    r_post = await client.post("/v1/auditoria", json={}, headers=headers)
    assert r_post.status_code == 405

    r_put = await client.put("/v1/auditoria", json={}, headers=headers)
    assert r_put.status_code == 405

    r_patch = await client.patch("/v1/auditoria", json={}, headers=headers)
    assert r_patch.status_code == 405

    r_delete = await client.delete("/v1/auditoria", headers=headers)
    assert r_delete.status_code == 405


async def test_filtros_de_auditoria(client, session):
    h_agente = await auth(client, "agente")
    h_delegado = await auth(client, "delegado")

    # Registrar ocorrência para gerar log
    oc = await registrar(client, h_agente)
    oc_id = oc["ocorrencia_id"]

    # Validar ocorrência para gerar log de validação
    r_val = await client.post(f"/v1/ocorrencias/{oc_id}/validar", headers=h_delegado)
    assert r_val.status_code == 200

    # 1. Filtro por entidade
    r_ent = await client.get("/v1/auditoria", params={"entidade": "Ocorrencia"}, headers=h_delegado)
    assert r_ent.status_code == 200
    itens_ent = r_ent.json()
    assert len(itens_ent) >= 2
    assert all(i["entidade"] == "Ocorrencia" for i in itens_ent)

    # 2. Filtro por operacao
    r_op = await client.get("/v1/auditoria", params={"operacao": "ocorrencia.validar"}, headers=h_delegado)
    assert r_op.status_code == 200
    itens_op = r_op.json()
    assert len(itens_op) >= 1
    assert all(i["operacao"] == "ocorrencia.validar" for i in itens_op)

    # 3. Filtro por entidade_id
    r_id = await client.get("/v1/auditoria", params={"entidade_id": oc_id}, headers=h_delegado)
    assert r_id.status_code == 200
    itens_id = r_id.json()
    assert len(itens_id) >= 2
    assert all(i["entidade_id"] == oc_id for i in itens_id)

    # 4. Filtro por quem
    r_quem = await client.get("/v1/auditoria", params={"quem": str(IDS["delegado"])}, headers=h_delegado)
    assert r_quem.status_code == 200
    itens_quem = r_quem.json()
    assert len(itens_quem) >= 1
    assert all(i["quem"] == str(IDS["delegado"]) for i in itens_quem)

    # 5. Validação de identificador_amigavel e autor_nome (enriquecimento na leitura)
    assert any(i.get("identificador_amigavel") == oc["numero_protocolo"] for i in itens_id)
    assert any(i.get("autor_nome") == "Delegado" and i.get("autor_papel") == "DELEGADO" for i in itens_quem)


async def test_mascaramento_cpf_em_payloads_de_auditoria(client, session):
    h_delegado = await auth(client, "delegado")

    # Inserir registro diretamente com dados contendo CPFs explícitos e no texto
    registro_id = uuid4()
    registro = RegistroAuditoriaModel(
        id=registro_id,
        quem=IDS["delegado"],
        quando=datetime.now(UTC),
        operacao="ocorrencia.registrar",
        entidade="Ocorrencia",
        entidade_id=str(uuid4()),
        dados_antes={"cpf": "12345678901", "detalhe": "Sem alterações prévias"},
        dados_depois={
            "documento": "987.654.321-00",
            "envolvido": {
                "cpf": "11122233344",
                "relato": "Cidadão portador do CPF 123.456.789-01 compareceu ao local.",
            },
            "outros_dados": "Sem dados sensíveis",
        },
        ip="127.0.0.1",
    )
    session.add(registro)
    await session.commit()

    # Consultar via API
    r = await client.get("/v1/auditoria", params={"entidade_id": registro.entidade_id}, headers=h_delegado)
    assert r.status_code == 200
    itens = r.json()
    assert len(itens) == 1
    item = itens[0]

    # Verificar que CPFs foram mascarados no formato ***.***.XYZ-**
    assert item["dados_antes"]["cpf"] == "***.***.789-**"
    assert item["dados_depois"]["documento"] == "***.***.321-**"
    assert item["dados_depois"]["envolvido"]["cpf"] == "***.***.333-**"
    assert "***.***.789-**" in item["dados_depois"]["envolvido"]["relato"]

    # Garantir que o CPF cru NÃO vazou em nenhuma parte da resposta HTTP
    resposta_str = r.text
    assert "12345678901" not in resposta_str
    assert "987.654.321-00" not in resposta_str
    assert "11122233344" not in resposta_str
    assert "123.456.789-01" not in resposta_str
