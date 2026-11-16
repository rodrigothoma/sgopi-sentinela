"""Testes unitários puros do LaudoMapper (sem banco de dados)."""
from datetime import UTC, datetime
from uuid import uuid4

from adapters.outbound.persistence.mappers import LaudoMapper
from domain.laudo.entity import LaudoPericial, StatusLaudo, TipoPericia
from infrastructure.database.models import LaudoPericialModel

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)


def test_laudo_to_model_e_to_domain_roundtrip() -> None:
    laudo_id = uuid4()
    solicitante_id = uuid4()
    perito_id = uuid4()
    laudo = LaudoPericial(
        id=laudo_id,
        numero_referencia="LP-2026-000001",
        tipo_pericia=TipoPericia.BALISTICA,
        descricao_solicitacao="Exame pericial balístico em projétil.",
        solicitante_id=solicitante_id,
        solicitado_em=AGORA,
        perito_id=perito_id,
        conclusoes_tecnicas="Calibre 9mm compatível com apreensão.",
        arquivo_chave="laudos/lp-2026-000001.pdf",
        arquivo_nome="laudo_balistica.pdf",
        hash_sha256="a" * 64,
        status=StatusLaudo.CONCLUIDO,
        concluido_em=AGORA,
        atualizado_em=AGORA,
        ativo=True,
        versao=3,
    )

    model = LaudoMapper.to_model(laudo)

    assert model.id == laudo_id
    assert model.numero_referencia == "LP-2026-000001"
    assert model.tipo_pericia == "BALISTICA"
    assert model.perito_id == perito_id
    assert model.hash_sha256 == "a" * 64
    assert model.status == "CONCLUIDO"
    assert model.versao == 3

    reconstituido = LaudoMapper.to_domain(model)

    assert reconstituido.id == laudo_id
    assert reconstituido.tipo_pericia == TipoPericia.BALISTICA
    assert reconstituido.status == StatusLaudo.CONCLUIDO
    assert reconstituido.conclusoes_tecnicas == "Calibre 9mm compatível com apreensão."
    assert reconstituido.versao == 3


def test_laudo_atualizar_model() -> None:
    laudo_id = uuid4()
    model = LaudoPericialModel(
        id=laudo_id,
        numero_referencia="LP-2026-000002",
        tipo_pericia="LOCAL_CRIME",
        descricao_solicitacao="Perícia em local de roubo.",
        solicitante_id=uuid4(),
        status="SOLICITADO",
        solicitado_em=AGORA,
        versao=1,
        ativo=True,
    )

    perito_id = uuid4()
    laudo_atualizado = LaudoPericial(
        id=laudo_id,
        numero_referencia="LP-2026-000002",
        tipo_pericia=TipoPericia.LOCAL_CRIME,
        descricao_solicitacao="Perícia em local de roubo.",
        solicitante_id=model.solicitante_id,
        solicitado_em=AGORA,
        perito_id=perito_id,
        conclusoes_tecnicas="Arrombamento comprovado na porta frontal.",
        status=StatusLaudo.CONCLUIDO,
        concluido_em=AGORA,
        atualizado_em=AGORA,
        ativo=True,
        versao=2,
    )

    LaudoMapper.atualizar_model(model, laudo_atualizado)

    assert model.perito_id == perito_id
    assert model.status == "CONCLUIDO"
    assert model.conclusoes_tecnicas == "Arrombamento comprovado na porta frontal."
    assert model.versao == 2


def test_laudo_roundtrip_preserva_todos_os_campos() -> None:
    laudo = LaudoPericial(
        numero_referencia="LP-2026-000003",
        tipo_pericia=TipoPericia.BALISTICA,
        descricao_solicitacao="Exame em arma apreendida.",
        solicitante_id=uuid4(),
        solicitado_em=AGORA,
        ocorrencia_id=uuid4(),
        inquerito_id=uuid4(),
        item_apreendido_id=uuid4(),
        atualizado_em=AGORA,
        versao=1,
    )

    assert LaudoMapper.to_domain(LaudoMapper.to_model(laudo)) == laudo


def test_laudo_to_domain_torna_aware_as_datas_naive_do_banco() -> None:
    """O SQLite devolve datetime sem fuso; o domínio só trabalha com instantes aware."""
    naive = AGORA.replace(tzinfo=None)
    model = LaudoPericialModel(
        id=uuid4(),
        numero_referencia="LP-2026-000004",
        tipo_pericia="LOCAL_CRIME",
        descricao_solicitacao="Perícia em local de roubo.",
        solicitante_id=uuid4(),
        status="SOLICITADO",
        solicitado_em=naive,
        concluido_em=None,
        atualizado_em=naive,
        versao=1,
        ativo=True,
    )

    laudo = LaudoMapper.to_domain(model)

    assert laudo.solicitado_em == AGORA
    assert laudo.atualizado_em == AGORA
    assert laudo.concluido_em is None
