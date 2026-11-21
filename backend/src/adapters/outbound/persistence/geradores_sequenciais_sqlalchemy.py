"""
Adapter de saída: GeradorNumeroSequencial sobre as tabelas ``sequencias_*`` (HEX-08).

Cada tipo de documento (protocolo, inquérito, laudo, medida, ordem de despacho, ofício) tem a sua
tabela com uma linha por ano; a numeração recomeça em 1 a cada virada de ano.
"""
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.gerador_numero_sequencial import (
    GeradorNumeroSequencial,
    TipoDocumentoSequencial,
    formatar_numero_sequencial,
)
from infrastructure.database.models import (
    SequenciaInqueritoModel,
    SequenciaLaudoModel,
    SequenciaMedidaModel,
    SequenciaOficioModel,
    SequenciaOrdemDespachoModel,
    SequenciaProtocoloModel,
)

_TABELAS: dict[TipoDocumentoSequencial, str] = {
    TipoDocumentoSequencial.PROTOCOLO: SequenciaProtocoloModel.__tablename__,
    TipoDocumentoSequencial.INQUERITO: SequenciaInqueritoModel.__tablename__,
    TipoDocumentoSequencial.LAUDO: SequenciaLaudoModel.__tablename__,
    TipoDocumentoSequencial.MEDIDA_PROTETIVA: SequenciaMedidaModel.__tablename__,
    TipoDocumentoSequencial.ORDEM_DESPACHO: SequenciaOrdemDespachoModel.__tablename__,
    TipoDocumentoSequencial.OFICIO: SequenciaOficioModel.__tablename__,
}


def montar_upsert_sequencia(tabela: str) -> TextClause:
    """Upsert atômico (``INSERT … ON CONFLICT DO UPDATE … RETURNING``) que incrementa o contador do ano.

    Válido em PostgreSQL e SQLite ≥ 3.35. O lock de linha do Postgres serializa transações
    concorrentes, inclusive na criação do primeiro número do ano (RF01* critério 3). O nome da
    tabela entra por interpolação no SQL, então só identificador simples é aceito.
    """
    if not tabela.isidentifier():
        raise ValueError(f"Nome de tabela de sequência inválido: {tabela!r}")
    return text(
        f"INSERT INTO {tabela} (ano, ultimo) VALUES (:ano, 1) "
        f"ON CONFLICT (ano) DO UPDATE SET ultimo = {tabela}.ultimo + 1 "
        "RETURNING ultimo"
    )


_UPSERTS: dict[TipoDocumentoSequencial, TextClause] = {
    tipo: montar_upsert_sequencia(tabela) for tipo, tabela in _TABELAS.items()
}


class GeradorSequencialSQLAlchemy(GeradorNumeroSequencial):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo(self, tipo: TipoDocumentoSequencial, ano: int) -> str:
        sequencial = (await self._session.execute(_UPSERTS[tipo], {"ano": ano})).scalar_one()
        return formatar_numero_sequencial(tipo, ano, int(sequencial))
