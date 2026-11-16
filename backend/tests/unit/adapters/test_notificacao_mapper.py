"""Testes unitários puros do NotificacaoMapper (sem banco de dados)."""
from datetime import UTC, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import NotificacaoMapper
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from infrastructure.database.models import NotificacaoModel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
AGORA_NAIVE = AGORA.replace(tzinfo=None)


def _notificacao() -> Notificacao:
    return Notificacao(
        titulo="Medida protetiva a vencer",
        mensagem="A medida MP-2026-000001 vence em 5 dias.",
        criada_em=AGORA,
        tipo=TipoNotificacao.VENCIMENTO_MEDIDA,
        prioridade=PrioridadeNotificacao.ALTA,
        usuario_id=uuid4(),
        papel_destinatario="DELEGADO",
        departamento_destinatario="POLICIA_CIVIL",
        link="/medidas/1",
        metadados={"medida_id": "1"},
    )


def test_notificacao_roundtrip_sem_leitura() -> None:
    notificacao = _notificacao()

    model = NotificacaoMapper.to_model(notificacao)

    assert model.id == notificacao.id
    assert model.tipo == "VENCIMENTO_MEDIDA"
    assert model.prioridade == "ALTA"
    assert model.metadados == {"medida_id": "1"}
    assert model.criada_em == AGORA

    assert NotificacaoMapper.to_domain(model, None) == notificacao


def test_to_model_nunca_grava_leitura_na_notificacao() -> None:
    """A leitura é individual e vive em notificacoes_leituras, não na linha da notificação."""
    notificacao = _notificacao()
    notificacao.lida, notificacao.lida_em = True, AGORA

    model = NotificacaoMapper.to_model(notificacao)

    assert model.lida is False
    assert model.lida_em is None


def test_to_domain_deriva_lida_do_instante_de_leitura_do_usuario() -> None:
    model = NotificacaoMapper.to_model(_notificacao())
    model.criada_em = AGORA_NAIVE

    notificacao = NotificacaoMapper.to_domain(model, AGORA_NAIVE)

    assert notificacao.lida is True
    assert notificacao.lida_em == AGORA
    assert notificacao.criada_em == AGORA


def test_to_domain_usa_padrao_para_tipo_e_prioridade_desconhecidos() -> None:
    model = NotificacaoModel(
        id=uuid4(),
        tipo="TIPO_REMOVIDO",
        titulo="Aviso antigo",
        mensagem="Registro gravado por uma versão anterior.",
        prioridade="URGENTISSIMA",
        criada_em=AGORA,
        ativo=True,
    )

    notificacao = NotificacaoMapper.to_domain(model, None)

    assert notificacao.tipo == TipoNotificacao.SISTEMA
    assert notificacao.prioridade == PrioridadeNotificacao.MEDIA


def test_atualizar_model_so_altera_o_ativo() -> None:
    notificacao = _notificacao()
    model = NotificacaoMapper.to_model(notificacao)
    notificacao.ativo = False
    notificacao.titulo = "Título que não deve ser regravado"

    NotificacaoMapper.atualizar_model(model, notificacao)

    assert model.ativo is False
    assert model.titulo == "Medida protetiva a vencer"
