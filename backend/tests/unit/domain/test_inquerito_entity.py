"""Testes unitários da entidade Inquerito (RF06 / UC06)."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.inquerito.entity import Inquerito, StatusInquerito
from domain.shared.exceptions import CampoObrigatorioError, ConflitoError, ValorInvalidoError


def test_instaurar_inquerito_sucesso():
    delegado_id = uuid4()
    agora = datetime.now(timezone.utc)
    inq = Inquerito.instaurar(
        numero="IP-2026-000001",
        ementa="Investigação de quadrilha de estelionato eletrônico na região central",
        delegado_id=delegado_id,
        instante=agora,
    )
    assert inq.numero == "IP-2026-000001"
    assert inq.status == StatusInquerito.EM_ANDAMENTO
    assert inq.delegado_id == delegado_id
    assert len(inq.ocorrencias_ids) == 0


def test_instaurar_inquerito_validacoes():
    agora = datetime.now(timezone.utc)
    with pytest.raises(CampoObrigatorioError):
        Inquerito.instaurar(
            numero="IP-2026-000001",
            ementa="Curta",  # menor que 10
            delegado_id=uuid4(),
            instante=agora,
        )

    with pytest.raises(CampoObrigatorioError):
        Inquerito.instaurar(
            numero="",
            ementa="Investigação detalhada com mais de dez caracteres",
            delegado_id=uuid4(),
            instante=agora,
        )


def test_vincular_e_desvincular_ocorrencias():
    agora = datetime.now(timezone.utc)
    inq = Inquerito.instaurar(
        numero="IP-2026-000001",
        ementa="Investigação de furto e receptação de veículos",
        delegado_id=uuid4(),
        instante=agora,
    )
    oc_id1 = uuid4()
    oc_id2 = uuid4()

    inq.vincular_ocorrencia(oc_id1, agora)
    assert inq.ocorrencias_ids == [oc_id1]

    # Idempotência
    inq.vincular_ocorrencia(oc_id1, agora)
    assert inq.ocorrencias_ids == [oc_id1]

    inq.vincular_ocorrencia(oc_id2, agora)
    assert inq.ocorrencias_ids == [oc_id1, oc_id2]

    inq.desvincular_ocorrencia(oc_id1, agora)
    assert inq.ocorrencias_ids == [oc_id2]


def test_concluir_e_arquivar_inquerito():
    agora = datetime.now(timezone.utc)
    inq = Inquerito.instaurar(
        numero="IP-2026-000001",
        ementa="Investigação criminal de roubo a estabelecimento comercial",
        delegado_id=uuid4(),
        instante=agora,
    )

    with pytest.raises(ValorInvalidoError):
        inq.concluir("Curto", agora)

    inq.concluir("Relatório conclusivo com indiciamento formal dos suspeitos", agora)
    assert inq.status == StatusInquerito.CONCLUIDO
    assert inq.concluido_em == agora

    # Não permite vincular ocorrências após conclusão
    with pytest.raises(ConflitoError):
        inq.vincular_ocorrencia(uuid4(), agora)


def _em_andamento() -> Inquerito:
    return Inquerito.instaurar(
        numero="IP-2026-000099", ementa="Ementa suficientemente longa", delegado_id=uuid4(), instante=datetime.now(timezone.utc)
    )


def test_arquivar_exige_motivo_e_status_em_andamento():
    agora = datetime.now(timezone.utc)
    i = _em_andamento()
    with pytest.raises(ValorInvalidoError):
        i.arquivar("curto", agora)
    i.arquivar("Ausência de justa causa para prosseguir.", agora)
    assert i.status == StatusInquerito.ARQUIVADO and i.concluido_em == agora
    with pytest.raises(ConflitoError):
        i.arquivar("Ausência de justa causa para prosseguir.", agora)
    with pytest.raises(ConflitoError):
        i.concluir("Relatório final detalhado.", agora)


def test_finalizado_nao_aceita_alterar_vinculos():
    agora = datetime.now(timezone.utc)
    i = _em_andamento()
    i.concluir("Relatório final detalhado do caso.", agora)
    with pytest.raises(ConflitoError):
        i.vincular_ocorrencia(uuid4(), agora)
    with pytest.raises(ConflitoError):
        i.desvincular_ocorrencia(uuid4(), agora)
    with pytest.raises(ValorInvalidoError):
        _em_andamento().concluir("curto", agora)


def test_reidratacao_sem_atualizado_em_usa_abertura():
    agora = datetime.now(timezone.utc)
    assert Inquerito(numero="IP-1", ementa="Ementa longa", delegado_id=uuid4(), data_abertura=agora).atualizado_em == agora
