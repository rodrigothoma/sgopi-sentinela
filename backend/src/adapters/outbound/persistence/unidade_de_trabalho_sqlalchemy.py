"""Adapter de saída: UnidadeDeTrabalhoSQLAlchemy — detém a transação da sessão (RNF11)."""
from sqlalchemy.ext.asyncio import AsyncSession

from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho


class UnidadeDeTrabalhoSQLAlchemy(UnidadeDeTrabalho):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
