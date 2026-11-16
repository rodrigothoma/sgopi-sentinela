"""Integração: geradores de número sequencial por ano (HEX-08) sobre o UPSERT atômico compartilhado."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.geradores_sequenciais_sqlalchemy import (
    GeradorNumeroInqueritoSQLAlchemy,
    GeradorNumeroLaudoSQLAlchemy,
    GeradorNumeroMedidaSQLAlchemy,
    GeradorNumeroOficioSQLAlchemy,
    GeradorNumeroOrdemSQLAlchemy,
    GeradorProtocoloSQLAlchemy,
    GeradorSequencialSQLAlchemy,
)

GERADORES_POR_PREFIXO = [
    (GeradorProtocoloSQLAlchemy, "SGOPI"),
    (GeradorNumeroInqueritoSQLAlchemy, "IP"),
    (GeradorNumeroLaudoSQLAlchemy, "LP"),
    (GeradorNumeroMedidaSQLAlchemy, "MP"),
    (GeradorNumeroOrdemSQLAlchemy, "OD"),
    (GeradorNumeroOficioSQLAlchemy, "OFI"),
]


@pytest.mark.parametrize(("classe", "prefixo"), GERADORES_POR_PREFIXO)
async def test_numeracao_sequencial_reinicia_a_cada_ano(
    session: AsyncSession, classe: type[GeradorSequencialSQLAlchemy], prefixo: str
) -> None:
    gerador = classe(session)

    assert await gerador.proximo(2026) == f"{prefixo}-2026-000001"
    assert await gerador.proximo(2026) == f"{prefixo}-2026-000002"
    assert await gerador.proximo(2027) == f"{prefixo}-2027-000001"
    await session.commit()
    assert await gerador.proximo(2026) == f"{prefixo}-2026-000003"


async def test_cada_gerador_tem_contador_proprio(session: AsyncSession) -> None:
    await GeradorProtocoloSQLAlchemy(session).proximo(2026)
    await GeradorProtocoloSQLAlchemy(session).proximo(2026)

    assert await GeradorNumeroLaudoSQLAlchemy(session).proximo(2026) == "LP-2026-000001"
    ultimo_laudo = (await session.execute(text("SELECT ultimo FROM sequencias_laudo WHERE ano = 2026"))).scalar_one()
    assert ultimo_laudo == 1


async def test_oficio_atende_a_porta_pelo_metodo_proximo_numero(session: AsyncSession) -> None:
    assert await GeradorNumeroOficioSQLAlchemy(session).proximo_numero(2026) == "OFI-2026-000001"


def test_tabela_com_nome_que_nao_e_identificador_e_recusada(session: AsyncSession) -> None:
    """O nome da tabela é interpolado no SQL: só identificador simples, nunca texto arbitrário."""
    with pytest.raises(ValueError):
        GeradorSequencialSQLAlchemy(session, "sequencias_laudo; DROP TABLE usuarios", lambda ano, seq: f"{ano}-{seq}")
