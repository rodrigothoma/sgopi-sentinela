"""Testes unitários da entidade MedidaProtetiva (RF09 / UC09)."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida, TipoRestricao
from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError


def test_conceder_medida_protetiva_sucesso():
    vitima_id = uuid4()
    agressor_id = uuid4()
    delegado_id = uuid4()
    oc_id = uuid4()
    agora = datetime.now(timezone.utc)
    hoje = agora.date()

    medida = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001",
        ocorrencia_id=oc_id,
        delegado_id=delegado_id,
        vitima_id=vitima_id,
        agressor_id=agressor_id,
        tipos_restricao=[TipoRestricao.AFASTAMENTO_DO_LAR.value, TipoRestricao.PROIBICAO_DE_CONTATO.value],
        data_inicio=hoje,
        prazo_dias=90,
        instante=agora,
        distancia_minima_metros=500,
    )
    assert medida.numero_referencia == "MP-2026-000001"
    assert medida.status == StatusMedida.ATIVA
    assert medida.prazo_dias == 90
    assert medida.data_vencimento == hoje + timedelta(days=90)
    assert medida.dias_restantes(hoje) == 90


def test_conceder_medida_validacoes():
    mesma_pessoa = uuid4()
    agora = datetime.now(timezone.utc)
    hoje = agora.date()

    # Vítima e agressor iguais
    with pytest.raises(ValorInvalidoError):
        MedidaProtetiva.conceder(
            numero_referencia="MP-2026-000001",
            ocorrencia_id=uuid4(),
            delegado_id=uuid4(),
            vitima_id=mesma_pessoa,
            agressor_id=mesma_pessoa,
            tipos_restricao=[TipoRestricao.PROIBICAO_DE_CONTATO.value],
            data_inicio=hoje,
            prazo_dias=60,
            instante=agora,
        )

    # Sem restrições
    with pytest.raises(CampoObrigatorioError):
        MedidaProtetiva.conceder(
            numero_referencia="MP-2026-000001",
            ocorrencia_id=uuid4(),
            delegado_id=uuid4(),
            vitima_id=uuid4(),
            agressor_id=uuid4(),
            tipos_restricao=[],
            data_inicio=hoje,
            prazo_dias=60,
            instante=agora,
        )


def test_renovar_e_revogar_medida():
    agora = datetime.now(timezone.utc)
    hoje = agora.date()
    medida = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=[TipoRestricao.PROIBICAO_DE_CONTATO.value],
        data_inicio=hoje,
        prazo_dias=60,
        instante=agora,
    )

    vencimento_original = medida.data_vencimento
    medida.renovar(
        dias_adicionais=30,
        justificativa="Permanência de ameaças veladas por meios digitais à vítima",
        instante=agora,
    )
    assert medida.status == StatusMedida.RENOVADA
    assert medida.prazo_dias == 90
    assert medida.data_vencimento == vencimento_original + timedelta(days=30)

    medida.revogar(motivo="Reconciliação amigável e homologação judicial de revogação", instante=agora)
    assert medida.status == StatusMedida.REVOGADA

    with pytest.raises(ConflitoError):
        medida.renovar(30, "Tentativa em medida revogada", agora)
