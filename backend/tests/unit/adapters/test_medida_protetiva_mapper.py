"""Testes unitários puros do MedidaProtetivaMapper (sem banco de dados)."""
from datetime import UTC, date, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import MedidaProtetivaMapper
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from infrastructure.database.models import MedidaProtetivaModel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
HOJE = date(2026, 11, 16)


def test_medida_protetiva_to_model_e_to_domain_roundtrip() -> None:
    medida_id = uuid4()
    medida = MedidaProtetiva(
        id=medida_id,
        numero_referencia="MP-2026-000001",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["AFASTAMENTO_DO_LAR", "LIMITE_DISTANCIA_METROS"],
        distancia_minima_metros=300,
        data_inicio=HOJE,
        prazo_dias=90,
        data_vencimento=date(2027, 2, 14),
        condicoes_especificas="Manter distância também do local de trabalho.",
        status=StatusMedida.ATIVA,
        criada_em=AGORA,
        atualizada_em=AGORA,
        ativo=True,
        versao=1,
    )

    model = MedidaProtetivaMapper.to_model(medida)

    assert model.id == medida_id
    assert model.numero_referencia == "MP-2026-000001"
    assert model.tipos_restricao == ["AFASTAMENTO_DO_LAR", "LIMITE_DISTANCIA_METROS"]
    assert model.distancia_minima_metros == 300
    assert model.status == "ATIVA"
    assert model.versao == 1

    reconstituida = MedidaProtetivaMapper.to_domain(model)

    assert reconstituida.id == medida_id
    assert reconstituida.numero_referencia == "MP-2026-000001"
    assert reconstituida.status == StatusMedida.ATIVA
    assert reconstituida.tipos_restricao == ["AFASTAMENTO_DO_LAR", "LIMITE_DISTANCIA_METROS"]
    assert reconstituida.distancia_minima_metros == 300
    assert reconstituida.versao == 1


def test_medida_protetiva_atualizar_model() -> None:
    medida_id = uuid4()
    model = MedidaProtetivaModel(
        id=medida_id,
        numero_referencia="MP-2026-000002",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["PROIBICAO_DE_CONTATO"],
        distancia_minima_metros=None,
        data_inicio=HOJE,
        prazo_dias=60,
        data_vencimento=date(2027, 1, 15),
        status="ATIVA",
        criada_em=AGORA,
        versao=1,
        ativo=True,
    )

    medida_atualizada = MedidaProtetiva(
        id=medida_id,
        numero_referencia="MP-2026-000002",
        ocorrencia_id=model.ocorrencia_id,
        delegado_id=model.delegado_id,
        vitima_id=model.vitima_id,
        agressor_id=model.agressor_id,
        tipos_restricao=["PROIBICAO_DE_CONTATO", "AFASTAMENTO_DO_LAR"],
        distancia_minima_metros=200,
        data_inicio=HOJE,
        prazo_dias=120,
        data_vencimento=date(2027, 3, 16),
        justificativa_renovacao="Reincidência de ameaças comprovada.",
        status=StatusMedida.RENOVADA,
        criada_em=AGORA,
        atualizada_em=AGORA,
        ativo=True,
        versao=2,
    )

    MedidaProtetivaMapper.atualizar_model(model, medida_atualizada)

    assert model.tipos_restricao == ["PROIBICAO_DE_CONTATO", "AFASTAMENTO_DO_LAR"]
    assert model.distancia_minima_metros == 200
    assert model.prazo_dias == 120
    assert model.status == "RENOVADA"
    assert model.justificativa_renovacao == "Reincidência de ameaças comprovada."
    assert model.versao == 2


def _medida() -> MedidaProtetiva:
    return MedidaProtetiva(
        numero_referencia="MP-2026-000003",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["PROIBICAO_DE_CONTATO"],
        distancia_minima_metros=None,
        data_inicio=HOJE,
        prazo_dias=30,
        data_vencimento=date(2026, 12, 16),
        status=StatusMedida.ATIVA,
        criada_em=AGORA,
        atualizada_em=AGORA,
        alerta_vencimento_enviado_em=AGORA,
    )


def test_medida_protetiva_roundtrip_preserva_todos_os_campos() -> None:
    medida = _medida()

    assert MedidaProtetivaMapper.to_domain(MedidaProtetivaMapper.to_model(medida)) == medida


def test_medida_protetiva_model_nao_compartilha_a_lista_de_restricoes() -> None:
    """Com a mesma lista nos dois lados, o ORM não percebe a mutação feita na entidade e não emite UPDATE."""
    medida = _medida()

    model = MedidaProtetivaMapper.to_model(medida)
    assert model.tipos_restricao is not medida.tipos_restricao

    MedidaProtetivaMapper.atualizar_model(model, medida)
    assert model.tipos_restricao is not medida.tipos_restricao


def test_medida_protetiva_to_domain_torna_aware_as_datas_naive_do_banco() -> None:
    """O SQLite devolve datetime sem fuso; o domínio só trabalha com instantes aware."""
    naive = AGORA.replace(tzinfo=None)
    model = MedidaProtetivaMapper.to_model(_medida())
    model.criada_em = naive
    model.atualizada_em = naive
    model.alerta_vencimento_enviado_em = naive

    medida = MedidaProtetivaMapper.to_domain(model)

    assert medida.criada_em == AGORA
    assert medida.atualizada_em == AGORA
    assert medida.alerta_vencimento_enviado_em == AGORA


def test_medida_protetiva_to_domain_mantem_datas_opcionais_nulas() -> None:
    model = MedidaProtetivaMapper.to_model(_medida())
    model.alerta_vencimento_enviado_em = None

    assert MedidaProtetivaMapper.to_domain(model).alerta_vencimento_enviado_em is None
