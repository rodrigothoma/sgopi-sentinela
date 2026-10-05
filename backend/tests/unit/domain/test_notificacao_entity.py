from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.shared.exceptions import CampoObrigatorioError


def test_criar_notificacao_com_sucesso():
    uid = uuid4()
    agora = datetime.now(UTC)
    notif = Notificacao.criar(
        titulo="Alerta de Criticidade",
        mensagem="Área com mais de 3 ocorrências nas últimas 24h",
        tipo=TipoNotificacao.ALERTA_CRITICIDADE,
        prioridade=PrioridadeNotificacao.ALTA,
        usuario_id=uid,
        papel_destinatario="SUPERVISOR",
        link="/painel",
        instante=agora,
    )
    assert notif.id is not None
    assert notif.titulo == "Alerta de Criticidade"
    assert notif.mensagem == "Área com mais de 3 ocorrências nas últimas 24h"
    assert notif.tipo == TipoNotificacao.ALERTA_CRITICIDADE
    assert notif.prioridade == PrioridadeNotificacao.ALTA
    assert notif.usuario_id == uid
    assert notif.papel_destinatario == "SUPERVISOR"
    assert notif.lida is False
    assert notif.lida_em is None
    assert notif.criada_em == agora


def test_marcar_notificacao_como_lida():
    notif = Notificacao.criar(
        titulo="Nova Ocorrência",
        mensagem="Ocorrência registrada no plantão",
        instante=datetime.now(UTC),
    )
    instante_leitura = datetime.now(UTC)
    notif.marcar_lida(instante_leitura)
    assert notif.lida is True
    assert notif.lida_em == instante_leitura


def test_validacao_titulo_curto():
    with pytest.raises(CampoObrigatorioError, match="título"):
        Notificacao.criar(titulo="Oi", mensagem="Mensagem válida longa", instante=datetime.now(UTC))


def test_validacao_mensagem_curta():
    with pytest.raises(CampoObrigatorioError, match="mensagem"):
        Notificacao.criar(titulo="Título válido", mensagem="Ops", instante=datetime.now(UTC))


@pytest.mark.parametrize(
    ("destino", "usuario", "papel", "esperado"),
    [
        ({"usuario_id": "u1"}, "u1", "AGENTE", True),
        ({"usuario_id": "u1"}, "u2", "AGENTE", False),
        ({"papel_destinatario": "DELEGADO"}, "u2", "DELEGADO", True),
        ({"papel_destinatario": "DELEGADO"}, "u2", "AGENTE", False),
        ({}, "u2", "AGENTE", True),
    ],
)
def test_destinada_a(destino, usuario, papel, esperado):
    n = Notificacao.criar(titulo="Aviso geral", mensagem="Mensagem de teste", instante=datetime.now(UTC), **destino)
    assert n.destinada_a(usuario, papel) is esperado
