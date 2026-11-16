"""Testes unitários puros do OrdemDespachoMapper (sem banco de dados)."""
from datetime import UTC, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import OrdemDespachoMapper
from domain.despacho.entity import OrdemDeDespacho
from infrastructure.database.models import OrdemDespachoModel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
AGORA_NAIVE = AGORA.replace(tzinfo=None)


def _ordem(**extras: object) -> OrdemDeDespacho:
    campos: dict[str, object] = {
        "numero": "OD-2026-000001",
        "ocorrencia_id": uuid4(),
        "viatura_id": uuid4(),
        "operador_id": uuid4(),
        "criada_em": AGORA,
    }
    return OrdemDeDespacho(**(campos | extras))  # type: ignore[arg-type]


def test_ordem_ativa_roundtrip() -> None:
    ordem = _ordem(observacoes="Apoio ao flagrante.", apoio=True)

    model = OrdemDespachoMapper.to_model(ordem)

    assert model.id == ordem.id
    assert model.numero == "OD-2026-000001"
    assert model.ocorrencia_id == ordem.ocorrencia_id
    assert model.viatura_id == ordem.viatura_id
    assert model.operador_id == ordem.operador_id
    assert model.criada_em == AGORA
    assert model.ativa is True
    assert model.encerrada_em is None
    assert model.apoio is True

    assert OrdemDespachoMapper.to_domain(model) == ordem


def test_atualizar_model_grava_o_encerramento() -> None:
    ordem = _ordem()
    model = OrdemDespachoMapper.to_model(ordem)

    ordem.encerrar(AGORA)
    OrdemDespachoMapper.atualizar_model(model, ordem)

    assert model.ativa is False
    assert model.encerrada_em == AGORA


def test_to_domain_torna_aware_as_datas_naive_do_banco() -> None:
    """O SQLite devolve datetime sem fuso; o domínio só trabalha com instantes aware."""
    model = OrdemDespachoModel(
        id=uuid4(),
        numero="OD-2026-000002",
        ocorrencia_id=uuid4(),
        viatura_id=uuid4(),
        operador_id=uuid4(),
        criada_em=AGORA_NAIVE,
        ativa=False,
        encerrada_em=AGORA_NAIVE,
        apoio=False,
    )

    ordem = OrdemDespachoMapper.to_domain(model)

    assert ordem.criada_em == AGORA
    assert ordem.encerrada_em == AGORA
