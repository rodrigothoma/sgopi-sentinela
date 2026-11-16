"""
Adapters de saída: geradores de número sequencial por ano (HEX-08).

Cada documento numerado (protocolo, inquérito, laudo, medida, ordem de despacho, ofício) tem a sua
tabela ``sequencias_*`` com uma linha por ano; a numeração recomeça em 1 a cada virada de ano.
"""
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.gerador_numero_inquerito import GeradorNumeroInquerito, formatar_numero_inquerito
from application.ports.outbound.gerador_numero_laudo import GeradorNumeroLaudo, formatar_numero_laudo
from application.ports.outbound.gerador_numero_medida import GeradorNumeroMedida, formatar_numero_medida
from application.ports.outbound.gerador_numero_ordem import GeradorNumeroOrdem, formatar_numero_ordem
from application.ports.outbound.gerador_protocolo import GeradorProtocolo, formatar_protocolo
from application.ports.outbound.repositorio_comunicacao_interagencias import GeradorNumeroOficio, formatar_numero_oficio
from infrastructure.database.models import (
    SequenciaInqueritoModel,
    SequenciaLaudoModel,
    SequenciaMedidaModel,
    SequenciaOficioModel,
    SequenciaOrdemDespachoModel,
    SequenciaProtocoloModel,
)

Formatador = Callable[[int, int], str]


class GeradorSequencialSQLAlchemy:
    """Contador por ano com upsert atômico (``INSERT … ON CONFLICT DO UPDATE … RETURNING``).

    Válido em PostgreSQL e SQLite ≥ 3.35. O lock de linha do Postgres serializa transações
    concorrentes, inclusive na criação do primeiro número do ano (RF01* critério 3).
    """

    def __init__(self, session: AsyncSession, tabela: str, formatar: Formatador) -> None:
        # O nome entra por interpolação no SQL: só identificador simples, vindo do __tablename__ do model.
        if not tabela.isidentifier():
            raise ValueError(f"Nome de tabela de sequência inválido: {tabela!r}")
        self._session = session
        self._formatar = formatar
        self._upsert = text(
            f"INSERT INTO {tabela} (ano, ultimo) VALUES (:ano, 1) "
            f"ON CONFLICT (ano) DO UPDATE SET ultimo = {tabela}.ultimo + 1 "
            "RETURNING ultimo"
        )

    async def proximo(self, ano: int) -> str:
        sequencial = (await self._session.execute(self._upsert, {"ano": ano})).scalar_one()
        return self._formatar(ano, int(sequencial))


class GeradorProtocoloSQLAlchemy(GeradorSequencialSQLAlchemy, GeradorProtocolo):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SequenciaProtocoloModel.__tablename__, formatar_protocolo)


class GeradorNumeroInqueritoSQLAlchemy(GeradorSequencialSQLAlchemy, GeradorNumeroInquerito):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SequenciaInqueritoModel.__tablename__, formatar_numero_inquerito)


class GeradorNumeroLaudoSQLAlchemy(GeradorSequencialSQLAlchemy, GeradorNumeroLaudo):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SequenciaLaudoModel.__tablename__, formatar_numero_laudo)


class GeradorNumeroMedidaSQLAlchemy(GeradorSequencialSQLAlchemy, GeradorNumeroMedida):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SequenciaMedidaModel.__tablename__, formatar_numero_medida)


class GeradorNumeroOrdemSQLAlchemy(GeradorSequencialSQLAlchemy, GeradorNumeroOrdem):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SequenciaOrdemDespachoModel.__tablename__, formatar_numero_ordem)


class GeradorNumeroOficioSQLAlchemy(GeradorSequencialSQLAlchemy, GeradorNumeroOficio):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SequenciaOficioModel.__tablename__, formatar_numero_oficio)

    async def proximo_numero(self, ano: int) -> str:
        """A porta de ofício nomeia a operação como ``proximo_numero``; a contagem é a mesma das demais."""
        return await self.proximo(ano)
