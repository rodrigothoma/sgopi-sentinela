"""
Porta de saída: UnidadeDeTrabalho (HEX-09 / RNF11).

Detém a transação; repositórios só fazem add/merge. O caso de uso decide
quando confirmar. Uso:

    async with uow:
        ...
        await uow.commit()
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType


class UnidadeDeTrabalho(ABC):
    async def __aenter__(self) -> UnidadeDeTrabalho:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
