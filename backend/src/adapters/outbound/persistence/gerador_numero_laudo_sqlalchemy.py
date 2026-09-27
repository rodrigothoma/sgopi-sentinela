"""
Adapter de saída: GeradorNumeroLaudoSQLAlchemy (RF07 / HEX-08).

Contador atômico por ano para formato LP-AAAA-NNNNNN.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.gerador_numero_laudo import GeradorNumeroLaudo, formatar_numero_laudo

_UPSERT = text(
    "INSERT INTO sequencias_laudo (ano, ultimo) VALUES (:ano, 1) "
    "ON CONFLICT (ano) DO UPDATE SET ultimo = sequencias_laudo.ultimo + 1 "
    "RETURNING ultimo"
)


class GeradorNumeroLaudoSQLAlchemy(GeradorNumeroLaudo):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo(self, ano: int) -> str:
        sequencial = (await self._session.execute(_UPSERT, {"ano": ano})).scalar_one()
        return formatar_numero_laudo(ano, int(sequencial))
