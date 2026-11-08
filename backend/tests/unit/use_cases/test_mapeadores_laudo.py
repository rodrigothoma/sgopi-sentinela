"""Caracterização da conversão de laudo pericial para o DTO de saída."""

from datetime import UTC, datetime
from uuid import UUID

from application.ports.inbound.interface_gerir_laudos import LaudoOutput
from application.use_cases.laudo._mapeadores import para_laudo_output
from domain.laudo.entity import LaudoPericial, TipoPericia

LAUDO_ID = UUID("10000000-0000-0000-0000-000000000001")
SOLICITANTE_ID = UUID("10000000-0000-0000-0000-000000000002")
PERITO_ID = UUID("10000000-0000-0000-0000-000000000003")
OCORRENCIA_ID = UUID("10000000-0000-0000-0000-000000000004")
INQUERITO_ID = UUID("10000000-0000-0000-0000-000000000005")
ITEM_ID = UUID("10000000-0000-0000-0000-000000000006")
SOLICITADO_EM = datetime(2026, 11, 8, 10, 30, tzinfo=UTC)
CONCLUIDO_EM = datetime(2026, 11, 8, 14, 45, tzinfo=UTC)
HASH_SHA256 = "a" * 64


def _laudo_solicitado() -> LaudoPericial:
    return LaudoPericial(
        id=LAUDO_ID,
        numero_referencia="LP-2026-000001",
        tipo_pericia=TipoPericia.BALISTICA,
        descricao_solicitacao="Exame de confronto balístico",
        solicitante_id=SOLICITANTE_ID,
        solicitado_em=SOLICITADO_EM,
        ocorrencia_id=OCORRENCIA_ID,
        inquerito_id=INQUERITO_ID,
        item_apreendido_id=ITEM_ID,
    )


def test_mapeia_laudo_solicitado_com_todos_os_campos() -> None:
    saida = para_laudo_output(_laudo_solicitado())

    assert saida == LaudoOutput(
        id=LAUDO_ID,
        numero_referencia="LP-2026-000001",
        tipo_pericia="BALISTICA",
        descricao_solicitacao="Exame de confronto balístico",
        solicitante_id=SOLICITANTE_ID,
        status="SOLICITADO",
        solicitado_em="2026-11-08T10:30:00+00:00",
        atualizado_em="2026-11-08T10:30:00+00:00",
        perito_id=None,
        ocorrencia_id=OCORRENCIA_ID,
        inquerito_id=INQUERITO_ID,
        item_apreendido_id=ITEM_ID,
        conclusoes_tecnicas=None,
        arquivo_nome=None,
        hash_sha256=None,
        concluido_em=None,
    )


def test_mapeia_laudo_concluido_com_todos_os_campos() -> None:
    laudo = _laudo_solicitado()
    laudo.anexar_laudo_concluido(
        perito_id=PERITO_ID,
        conclusoes_tecnicas="Confronto balístico positivo.",
        arquivo_chave="laudos/laudo.pdf",
        arquivo_nome="laudo.pdf",
        hash_sha256=HASH_SHA256,
        instante=CONCLUIDO_EM,
    )

    saida = para_laudo_output(laudo)

    assert saida == LaudoOutput(
        id=LAUDO_ID,
        numero_referencia="LP-2026-000001",
        tipo_pericia="BALISTICA",
        descricao_solicitacao="Exame de confronto balístico",
        solicitante_id=SOLICITANTE_ID,
        status="CONCLUIDO",
        solicitado_em="2026-11-08T10:30:00+00:00",
        atualizado_em="2026-11-08T14:45:00+00:00",
        perito_id=PERITO_ID,
        ocorrencia_id=OCORRENCIA_ID,
        inquerito_id=INQUERITO_ID,
        item_apreendido_id=ITEM_ID,
        conclusoes_tecnicas="Confronto balístico positivo.",
        arquivo_nome="laudo.pdf",
        hash_sha256=HASH_SHA256,
        concluido_em="2026-11-08T14:45:00+00:00",
    )


def test_atualizado_em_usa_data_da_solicitacao_como_fallback() -> None:
    laudo = _laudo_solicitado()
    laudo.atualizado_em = None

    saida = para_laudo_output(laudo)

    assert saida.atualizado_em == saida.solicitado_em == "2026-11-08T10:30:00+00:00"
