"""
Adapter de saída: GeradorNumeroMedidaSQLAlchemy (RF09 / HEX-08).

Contador atômico por ano para formato MP-AAAA-NNNNNN.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.gerador_numero_medida import GeradorNumeroMedida, formatar_numero_medida

_UPSERT = text(
    "INSERT INTO sequencias_medida (ano, ultimo) VALUES (:ano, 1) "
    "ON CONFLICT (ano) DO UPDATE SET ultimo = sequencias_medida.ultimo + 1 "
    "RETURNING ultimo"
)


class GeradorNumeroMedidaSQLAlchemy(GeradorNumeroMedida):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo(self, ano: int) -> str:
        sequencial = (await self._session.execute(_UPSERT, {"ano": ano})).scalar_one()
        return formatar_numero_medida(ano, int(sequencial))
