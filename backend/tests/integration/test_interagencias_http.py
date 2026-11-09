"""Integração HTTP: Comunicação Interagências (RF11 / UC15)."""
from tests.integration.helpers import auth, registrar


async def test_fluxo_comunicacao_interagencias(client):
    h_delegado = await auth(client, "delegado")
    h_agente = await auth(client, "agente")

    # 1. Listar departamentos
    res_depts = await client.get("/v1/interagencias/departamentos", headers=h_agente)
    assert res_depts.status_code == 200
    depts = res_depts.json()
    assert len(depts) == 6
    codigos = [d["codigo"] for d in depts]
    assert "POLICIA_CIVIL" in codigos
    assert "POLICIA_MILITAR" in codigos
    assert "POLICIA_CIENTIFICA" in codigos

    # 2. Registrar uma ocorrência para associar ao ofício
    oc = await registrar(client, h_agente)
    protocolo = oc["numero_protocolo"]

    # 3. Agente comum tenta enviar ofício interagências -> 403
    payload = {
        "departamento_origem": "POLICIA_CIVIL",
        "departamentos_destinatarios": ["POLICIA_CIENTIFICA"],
        "assunto": "Solicitação de Perícia Balística Complementar",
        "corpo": "Encaminhamento de projéteis recolhidos para confronto microscópico.",
        "prioridade": "URGENTE",
        "nivel_sigilo": "CONFIDENCIAL",
        "protocolo_ocorrencia": protocolo,
    }
    res_negado = await client.post("/v1/interagencias", json=payload, headers=h_agente)
    assert res_negado.status_code == 403

    # 4. Delegado envia comunicação interagências -> 201
    res_envio = await client.post("/v1/interagencias", json=payload, headers=h_delegado)
    assert res_envio.status_code == 201, res_envio.text
    comunicacao = res_envio.json()
    assert comunicacao["numero_oficio"].startswith("OFI-")
    assert comunicacao["departamento_origem"] == "POLICIA_CIVIL"
    assert comunicacao["departamentos_destinatarios"] == ["POLICIA_CIENTIFICA"]
    assert comunicacao["prioridade"] == "URGENTE"
    comunicacao_id = comunicacao["id"]

    # 5. Responder / despachar na thread
    res_resposta = await client.post(
        f"/v1/interagencias/{comunicacao_id}/responder",
        json={
            "departamento_origem": "POLICIA_CIENTIFICA",
            "assunto": "Resposta ao Ofício de Perícia Balística",
            "corpo": "Material pericial recebido pelo Instituto de Criminalística sob protocolo IC-982.",
            "prioridade": "URGENTE",
        },
        headers=h_delegado,
    )
    assert res_resposta.status_code == 200
    atualizada = res_resposta.json()
    assert atualizada["numero_oficio"].startswith("OFI-")
    assert atualizada["mensagem_pai_id"] == comunicacao_id

    # 6. Listar comunicações filtrando por departamento
    res_list = await client.get("/v1/interagencias?departamento=POLICIA_CIENTIFICA", headers=h_delegado)
    assert res_list.status_code == 200
    dados_list = res_list.json()
    assert len(dados_list) >= 1
    assert any(c["id"] == comunicacao_id for c in dados_list)



async def _enviar(client, headers, nivel: str, assunto: str) -> dict:
    r = await client.post(
        "/v1/interagencias",
        json={
            "departamento_origem": "POLICIA_CIVIL",
            "departamentos_destinatarios": ["POLICIA_MILITAR"],
            "assunto": assunto,
            "corpo": "Conteúdo operacional do ofício para teste de sigilo.",
            "nivel_sigilo": nivel,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _assuntos_visiveis(client, login: str) -> set[str]:
    r = await client.get("/v1/interagencias", headers=await auth(client, login))
    assert r.status_code == 200, r.text
    return {c["assunto"] for c in r.json()}


async def test_listagem_respeita_nivel_de_sigilo_por_papel(client):
    """Regressão: qualquer usuário logado lia ofícios RESERVADO e CONFIDENCIAL."""
    h_delegado = await auth(client, "delegado")
    await _enviar(client, h_delegado, "PADRAO", "Ofício padrão de teste")
    await _enviar(client, h_delegado, "RESERVADO", "Ofício reservado de teste")
    await _enviar(client, h_delegado, "CONFIDENCIAL", "Ofício confidencial de teste")

    todos = {"Ofício padrão de teste", "Ofício reservado de teste", "Ofício confidencial de teste"}
    assert await _assuntos_visiveis(client, "supervisor") == todos
    assert await _assuntos_visiveis(client, "operador") == {"Ofício padrão de teste", "Ofício reservado de teste"}
    assert await _assuntos_visiveis(client, "agente") == {"Ofício padrão de teste"}
    assert await _assuntos_visiveis(client, "perito") == {"Ofício padrão de teste"}


async def test_resposta_a_oficio_sem_acesso_responde_404(client):
    h_delegado = await auth(client, "delegado")
    confidencial = await _enviar(client, h_delegado, "CONFIDENCIAL", "Ofício confidencial de teste")

    r = await client.post(
        f"/v1/interagencias/{confidencial['id']}/responder",
        json={"departamento_origem": "POLICIA_MILITAR", "assunto": "Resposta", "corpo": "Tentativa de resposta sem acesso."},
        headers=await auth(client, "operador"),
    )

    assert r.status_code == 404
    assert r.json()["code"] == "interagencias.nao_encontrada"
