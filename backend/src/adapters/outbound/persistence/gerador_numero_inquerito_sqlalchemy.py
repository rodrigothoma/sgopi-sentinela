"""
Adapter de saída: GeradorNumeroInqueritoSQLAlchemy (RF06 / HEX-08).

Contador atômico por ano para formato IP-AAAA-NNNNNN.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.gerador_numero_inquerito import GeradorNumeroInquerito, formatar_numero_inquerito

_UPSERT = text(
    "INSERT INTO sequencias_inquerito (ano, ultimo) VALUES (:ano, 1) "
    "ON CONFLICT (ano) DO UPDATE SET ultimo = sequencias_inquerito.ultimo + 1 "
    "RETURNING ultimo"
)


class GeradorNumeroInqueritoSQLAlchemy(GeradorNumeroInquerito):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo(self, ano: int) -> str:
        sequencial = (await self._session.execute(_UPSERT, {"ano": ano})).scalar_one()
        return formatar_numero_inquerito(ano, int(sequencial))
