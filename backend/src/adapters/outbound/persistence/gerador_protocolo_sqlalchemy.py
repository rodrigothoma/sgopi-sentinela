"""
Adapter de saída: GeradorProtocoloSQLAlchemy (HEX-08).

Contador por ano com upsert atômico (``INSERT … ON CONFLICT DO UPDATE … RETURNING``),
válido em PostgreSQL e SQLite ≥ 3.35. O lock de linha do Postgres serializa
inserções concorrentes (RF01* critério 3).
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.gerador_protocolo import GeradorProtocolo, formatar_protocolo

_UPSERT = text(
    "INSERT INTO sequencias_protocolo (ano, ultimo) VALUES (:ano, 1) "
    "ON CONFLICT (ano) DO UPDATE SET ultimo = sequencias_protocolo.ultimo + 1 "
    "RETURNING ultimo"
)


class GeradorProtocoloSQLAlchemy(GeradorProtocolo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo(self, ano: int) -> str:
        sequencial = (await self._session.execute(_UPSERT, {"ano": ano})).scalar_one()
        return formatar_protocolo(ano, int(sequencial))
