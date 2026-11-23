"""Integração: GeradorSequencialSQLAlchemy (HEX-08) — um UPSERT atômico por tipo de documento."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.geradores_sequenciais_sqlalchemy import (
    GeradorSequencialSQLAlchemy,
    montar_upsert_sequencia,
)
from application.ports.outbound.gerador_numero_sequencial import TipoDocumentoSequencial

PREFIXO_POR_TIPO = {
    TipoDocumentoSequencial.PROTOCOLO: "SGOPI",
    TipoDocumentoSequencial.INQUERITO: "IP",
    TipoDocumentoSequencial.LAUDO: "LP",
    TipoDocumentoSequencial.MEDIDA_PROTETIVA: "MP",
    TipoDocumentoSequencial.ORDEM_DESPACHO: "OD",
    TipoDocumentoSequencial.OFICIO: "OFI",
}


def test_todo_tipo_de_documento_tem_prefixo_esperado() -> None:
    assert set(PREFIXO_POR_TIPO) == set(TipoDocumentoSequencial)


@pytest.mark.parametrize(("tipo", "prefixo"), PREFIXO_POR_TIPO.items())
async def test_numeracao_sequencial_reinicia_a_cada_ano(
    session: AsyncSession, tipo: TipoDocumentoSequencial, prefixo: str
) -> None:
    gerador = GeradorSequencialSQLAlchemy(session)

    assert await gerador.proximo(tipo, 2026) == f"{prefixo}-2026-000001"
    assert await gerador.proximo(tipo, 2026) == f"{prefixo}-2026-000002"
    assert await gerador.proximo(tipo, 2027) == f"{prefixo}-2027-000001"
    await session.commit()
    assert await gerador.proximo(tipo, 2026) == f"{prefixo}-2026-000003"


async def test_cada_tipo_tem_contador_proprio(session: AsyncSession) -> None:
    gerador = GeradorSequencialSQLAlchemy(session)
    await gerador.proximo(TipoDocumentoSequencial.PROTOCOLO, 2026)
    await gerador.proximo(TipoDocumentoSequencial.PROTOCOLO, 2026)

    assert await gerador.proximo(TipoDocumentoSequencial.LAUDO, 2026) == "LP-2026-000001"
    ultimo_laudo = (await session.execute(text("SELECT ultimo FROM sequencias_laudo WHERE ano = 2026"))).scalar_one()
    assert ultimo_laudo == 1


def test_tabela_com_nome_que_nao_e_identificador_e_recusada() -> None:
    """O nome da tabela é interpolado no SQL: só identificador simples, nunca texto arbitrário."""
    with pytest.raises(ValueError):
        montar_upsert_sequencia("sequencias_laudo; DROP TABLE usuarios")
