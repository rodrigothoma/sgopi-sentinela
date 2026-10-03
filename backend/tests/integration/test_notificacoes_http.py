from datetime import datetime, UTC
from uuid import UUID, uuid4

from adapters.outbound.persistence.notificacao_repositorio_sqlalchemy import NotificacaoRepositorioSQLAlchemy
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from tests.integration.helpers import auth


async def test_fluxo_notificacoes_in_app(client, session_factory):
    h_agente = await auth(client, "agente")
    h_supervisor = await auth(client, "supervisor")

    # Obter id do agente logado a partir do token
    res_me = await client.get("/v1/usuarios", headers=h_agente)
    usuarios = res_me.json()
    agente_user = next(u for u in usuarios if u["login"] == "agente")
    agente_id = agente_user["id"]

    # Injeta 2 notificações para o agente diretamente via repositório
    now = datetime.now(UTC)
    async with session_factory() as s:
        repo = NotificacaoRepositorioSQLAlchemy(s)
        n1 = Notificacao(
            id=uuid4(),
            usuario_id=UUID(agente_id),
            titulo="Alerta Tático",
            mensagem="Atenção à área central da cidade",
            tipo=TipoNotificacao.ALERTA_CRITICIDADE,
            prioridade=PrioridadeNotificacao.ALTA,
            criada_em=now,
        )
        n2 = Notificacao(
            id=uuid4(),
            usuario_id=UUID(agente_id),
            titulo="Novo Despacho",
            mensagem="Você foi alocado em uma ocorrência",
            tipo=TipoNotificacao.SISTEMA,
            prioridade=PrioridadeNotificacao.MEDIA,
            criada_em=now,
        )
        await repo.salvar(n1)
        await repo.salvar(n2)
        await s.commit()

    # 1. Resumo de não lidas (badge)
    res_resumo = await client.get("/v1/notificacoes/resumo", headers=h_agente)
    assert res_resumo.status_code == 200
    assert res_resumo.json()["nao_lidas"] >= 2

    # 2. Listagem de notificações
    res_lista = await client.get("/v1/notificacoes", headers=h_agente)
    assert res_lista.status_code == 200
    dados = res_lista.json()
    assert dados["total"] >= 2
    assert dados["nao_lidas"] >= 2
    assert len(dados["itens"]) >= 2
    primeira = dados["itens"][0]
    assert primeira["lida"] is False

    # 3. Marcar uma como lida
    res_lida = await client.patch(f"/v1/notificacoes/{primeira['id']}/lida", headers=h_agente)
    assert res_lida.status_code == 200
    assert res_lida.json()["lida"] is True

    # 4. Marcar todas como lidas
    res_todas = await client.post("/v1/notificacoes/marcar-todas-lidas", headers=h_agente)
    assert res_todas.status_code == 200
    assert res_todas.json()["atualizadas"] >= 1

    # 5. Conferir resumo agora = 0 não lidas
    res_resumo2 = await client.get("/v1/notificacoes/resumo", headers=h_agente)
    assert res_resumo2.status_code == 200
    assert res_resumo2.json()["nao_lidas"] == 0
