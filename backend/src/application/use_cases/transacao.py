"""Execução opcional numa unidade de trabalho, para casos de uso que ainda aceitam ``uow=None``."""
from __future__ import annotations

from collections.abc import Awaitable, Callable

from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho


async def executar_em_transacao[T](uow: UnidadeDeTrabalho | None, operacao: Callable[[], Awaitable[T]]) -> T:
    """Roda ``operacao`` e confirma na UoW; sem UoW, só roda (a gravação fica com quem chamou).

    Evita duplicar o mesmo bloco de gravação nos ramos com e sem UoW. Quando a UoW passar a
    ser obrigatória nesses casos de uso (Onda 2 do plano de refatoração), este helper sai.
    """
    if uow is None:
        return await operacao()
    async with uow:
        resultado = await operacao()
        await uow.commit()
    return resultado
