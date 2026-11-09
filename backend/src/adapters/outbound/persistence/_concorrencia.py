"""Controle de concorrência otimista (RNF03) para repositórios SQLAlchemy via SELECT ... FOR UPDATE."""
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.shared.exceptions import ConflitoError


class _ModelVersionado(Protocol):
    """Protocolo estrutural para modelos ORM com chave primária e controle de versão."""

    id: Any
    versao: Any


class ControleVersaoMixin:
    """Mixin para repositórios SQLAlchemy com controle de concorrência otimista (RNF03)."""

    _session: AsyncSession

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._versoes_carregadas: dict[UUID, int] = {}

    def _registrar_versao(self, entidade_id: UUID, versao: int) -> None:
        """Registra a versão da entidade observada no momento da leitura ou escrita."""
        self._versoes_carregadas[entidade_id] = versao

    async def _verificar_versao(
        self,
        model_cls: type[_ModelVersionado],
        entidade_id: UUID,
        versao_entidade: int,
        mensagem: str,
    ) -> None:
        """Verifica se a entidade sofreu alteração concorrente antes de persistir mutações.

        Raises:
            ConflitoError: Se a versão no banco divergir da versão carregada ou for mais recente.
        """
        stmt = select(model_cls.versao).where(model_cls.id == entidade_id).with_for_update()
        versao_banco: int = (await self._session.execute(stmt)).scalar_one()
        versao_esperada = self._versoes_carregadas.get(entidade_id, versao_banco)

        if versao_banco != versao_esperada or versao_entidade < versao_banco:
            raise ConflitoError(
                mensagem,
                chave="generic.versao_desatualizada",
                versao_atual=versao_banco,
            )
