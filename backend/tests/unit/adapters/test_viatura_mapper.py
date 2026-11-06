"""Testes unitários puros do ViaturaMapper (sem dependência de banco de dados)."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import ViaturaMapper
from domain.shared.geo import Coordenada
from domain.viatura.entity import Posicao, SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def test_viatura_com_posicao_round_trip() -> None:
    """Valida conversão bidirecional de viatura com telemetria e posição geodésica."""
    v_id = uuid4()
    posicao = Posicao(coordenada=Coordenada(-29.78, -55.79), registrada_em=AGORA)
    viatura = Viatura(
        id=v_id,
        prefixo="V-01",
        placa="ABC1D23",
        situacao=SituacaoViatura.DISPONIVEL,
        ultima_posicao=posicao,
        versao=3,
        atualizada_em=AGORA,
    )

    model = ViaturaMapper.to_model(viatura)

    assert model.id == v_id
    assert model.prefixo == "V-01"
    assert model.placa == "ABC1D23"
    assert model.situacao == SituacaoViatura.DISPONIVEL.value
    assert model.latitude == -29.78
    assert model.longitude == -55.79
    assert model.posicao_registrada_em == AGORA
    assert model.versao == 3

    reconstituida = ViaturaMapper.to_domain(model)

    assert reconstituida.id == v_id
    assert reconstituida.prefixo == "V-01"
    assert reconstituida.situacao == SituacaoViatura.DISPONIVEL
    assert reconstituida.ultima_posicao is not None
    assert reconstituida.ultima_posicao.coordenada == Coordenada(-29.78, -55.79)
    assert reconstituida.ultima_posicao.registrada_em == AGORA


def test_viatura_sem_posicao_round_trip() -> None:
    """Valida que viatura recém-cadastrada ou sem sinal GPS (ultima_posicao=None) é mapeada corretamente."""
    v_id = uuid4()
    viatura = Viatura(
        id=v_id,
        prefixo="V-02",
        placa="XYZ9K88",
        situacao=SituacaoViatura.INDISPONIVEL,
        ultima_posicao=None,
        versao=1,
        atualizada_em=None,
    )

    model = ViaturaMapper.to_model(viatura)

    assert model.id == v_id
    assert model.latitude is None
    assert model.longitude is None
    assert model.posicao_registrada_em is None

    reconstituida = ViaturaMapper.to_domain(model)

    assert reconstituida.id == v_id
    assert reconstituida.prefixo == "V-02"
    assert reconstituida.situacao == SituacaoViatura.INDISPONIVEL
    assert reconstituida.ultima_posicao is None


def test_atualizar_model_viatura() -> None:
    """Valida sincronização de modelo existente ao alterar status e telemetria."""
    model = ViaturaModel(
        id=uuid4(),
        prefixo="V-03",
        placa="BRA2E19",
        situacao=SituacaoViatura.DISPONIVEL.value,
        versao=1,
        latitude=None,
        longitude=None,
        posicao_registrada_em=None,
    )

    nova_posicao = Posicao(coordenada=Coordenada(-29.75, -55.70), registrada_em=AGORA)
    viatura_atualizada = Viatura(
        id=model.id,
        prefixo="V-03",
        placa="BRA2E19",
        situacao=SituacaoViatura.EM_DESLOCAMENTO,
        ultima_posicao=nova_posicao,
        versao=2,
        atualizada_em=AGORA,
    )

    ViaturaMapper.atualizar_model(model, viatura_atualizada)

    assert model.situacao == SituacaoViatura.EM_DESLOCAMENTO.value
    assert model.versao == 2
    assert model.latitude == -29.75
    assert model.longitude == -55.70
    assert model.posicao_registrada_em == AGORA

