"""Testes unitários puros do InqueritoMapper (sem banco de dados)."""
from datetime import UTC, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import InqueritoMapper
from domain.inquerito.entity import Inquerito, StatusInquerito
from infrastructure.database.models import InqueritoModel, OcorrenciaModel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)


def test_inquerito_to_model_e_to_domain_roundtrip() -> None:
    inq_id = uuid4()
    del_id = uuid4()
    inquerito = Inquerito(
        id=inq_id,
        numero="IP-2026-000001",
        ementa="Investigação de furto qualificado continuado.",
        delegado_id=del_id,
        status=StatusInquerito.EM_ANDAMENTO,
        data_abertura=AGORA,
        relatorio_final="Relatório preliminar anexado.",
        motivo_arquivamento=None,
        concluido_em=None,
        atualizado_em=AGORA,
        ativo=True,
        versao=2,
    )

    model = InqueritoMapper.to_model(inquerito)

    assert model.id == inq_id
    assert model.numero == "IP-2026-000001"
    assert model.ementa == "Investigação de furto qualificado continuado."
    assert model.delegado_id == del_id
    assert model.status == "EM_ANDAMENTO"
    assert model.versao == 2
    assert model.ativo is True

    # Simula ocorrências vinculadas carregadas no model pelo ORM (filtrando EXCLUIDA)
    oc1 = OcorrenciaModel(id=uuid4(), status="VALIDADA")
    oc2 = OcorrenciaModel(id=uuid4(), status="EXCLUIDA")
    model.ocorrencias = [oc1, oc2]

    reconstituido = InqueritoMapper.to_domain(model)

    assert reconstituido.id == inq_id
    assert reconstituido.numero == "IP-2026-000001"
    assert reconstituido.status == StatusInquerito.EM_ANDAMENTO
    assert reconstituido.ocorrencias_ids == [oc1.id]  # oc2 excluída foi filtrada
    assert reconstituido.versao == 2


def test_inquerito_atualizar_model() -> None:
    inq_id = uuid4()
    model = InqueritoModel(
        id=inq_id,
        numero="IP-2026-000002",
        ementa="Ementa original com mais de dez caracteres",
        delegado_id=uuid4(),
        status="EM_ANDAMENTO",
        data_abertura=AGORA,
        versao=1,
        ativo=True,
    )

    inquerito_atualizado = Inquerito(
        id=inq_id,
        numero="IP-2026-000002",
        ementa="Ementa retificada com nova linha de investigação",
        delegado_id=model.delegado_id,
        status=StatusInquerito.CONCLUIDO,
        data_abertura=AGORA,
        relatorio_final="Concluído com indiciamento.",
        concluido_em=AGORA,
        atualizado_em=AGORA,
        ativo=True,
        versao=2,
    )

    InqueritoMapper.atualizar_model(model, inquerito_atualizado)

    assert model.ementa == "Ementa retificada com nova linha de investigação"
    assert model.status == "CONCLUIDO"
    assert model.relatorio_final == "Concluído com indiciamento."
    assert model.concluido_em == AGORA
    assert model.versao == 2


def test_inquerito_roundtrip_preserva_todos_os_campos() -> None:
    inquerito = Inquerito(
        numero="IP-2026-000003",
        ementa="Apuração de estelionato em série.",
        delegado_id=uuid4(),
        status=StatusInquerito.ARQUIVADO,
        data_abertura=AGORA,
        motivo_arquivamento="Autoria não identificada.",
        atualizado_em=AGORA,
        ativo=False,
        versao=4,
    )

    assert InqueritoMapper.to_domain(InqueritoMapper.to_model(inquerito)) == inquerito


def test_inquerito_to_domain_torna_aware_as_datas_naive_do_banco() -> None:
    """O SQLite devolve datetime sem fuso; o domínio só trabalha com instantes aware."""
    naive = AGORA.replace(tzinfo=None)
    model = InqueritoModel(
        id=uuid4(),
        numero="IP-2026-000004",
        ementa="Ementa com mais de dez caracteres",
        delegado_id=uuid4(),
        status="CONCLUIDO",
        data_abertura=naive,
        concluido_em=naive,
        atualizado_em=naive,
        versao=1,
        ativo=True,
    )

    inquerito = InqueritoMapper.to_domain(model)

    assert inquerito.data_abertura == AGORA
    assert inquerito.concluido_em == AGORA
    assert inquerito.atualizado_em == AGORA
    assert inquerito.ocorrencias_ids == []


def test_inquerito_to_domain_mantem_datas_opcionais_nulas() -> None:
    model = InqueritoModel(
        id=uuid4(),
        numero="IP-2026-000005",
        ementa="Ementa com mais de dez caracteres",
        delegado_id=uuid4(),
        status="EM_ANDAMENTO",
        data_abertura=AGORA,
        concluido_em=None,
        atualizado_em=AGORA,
        versao=1,
        ativo=True,
    )

    assert InqueritoMapper.to_domain(model).concluido_em is None
