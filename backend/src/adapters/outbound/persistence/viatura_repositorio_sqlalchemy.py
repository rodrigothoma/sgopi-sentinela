"""Adapter de saída: ViaturaRepositorioSQLAlchemy (RF02) com optimistic locking por ``versao``."""
from __future__ import annotations

from typing import overload
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._concorrencia import ControleVersaoMixin
from adapters.outbound.persistence.mappers import ViaturaMapper
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.viatura.entity import SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel


class ViaturaRepositorioSQLAlchemy(ControleVersaoMixin, RepositorioViatura):
    """Repositório de viaturas policiais com persistência relacional via SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        super().__init__()

    @overload
    def _reconstituir(self, model: None) -> None: ...

    @overload
    def _reconstituir(self, model: ViaturaModel) -> Viatura: ...

    def _reconstituir(self, model: ViaturaModel | None) -> Viatura | None:
        """Registra a versão atual para controle otimista e converte o model para entidade."""
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return ViaturaMapper.to_domain(model)

    async def salvar(self, viatura: Viatura) -> None:
        """Persiste viatura com verificação de concorrência otimista (RF02/RNF03).

        Raises:
            ConflitoError: Se a viatura foi alterada por outro usuário no banco de dados.
        """
        model = await self._session.get(ViaturaModel, viatura.id)
        if model is None:
            model = ViaturaMapper.to_model(viatura)
            self._session.add(model)
        else:
            await self._verificar_versao(
                ViaturaModel,
                viatura.id,
                viatura.versao,
                "A viatura foi alterada por outro usuário; recarregue e tente novamente.",
            )
            ViaturaMapper.atualizar_model(model, viatura)

        await self._session.flush()
        self._registrar_versao(viatura.id, viatura.versao)

    async def buscar_por_id(self, viatura_id: UUID) -> Viatura | None:
        """Localiza viatura pelo UUID primário."""
        return self._reconstituir(await self._session.get(ViaturaModel, viatura_id))

    async def buscar_por_prefixo(self, prefixo: str) -> Viatura | None:
        """Localiza viatura pelo prefixo tático oficial (ex: 'V-01', case-insensitive)."""
        model = (await self._session.execute(select(ViaturaModel).where(ViaturaModel.prefixo == prefixo.upper()))).scalar_one_or_none()
        return self._reconstituir(model)

    async def buscar_por_placa(self, placa: str) -> Viatura | None:
        """Localiza viatura pela placa veicular oficial."""
        model = (await self._session.execute(select(ViaturaModel).where(ViaturaModel.placa == placa.upper()))).scalar_one_or_none()
        return self._reconstituir(model)

    async def listar(self, situacoes: tuple[SituacaoViatura, ...] = ()) -> list[Viatura]:
        """Lista viaturas ordenadas por prefixo, com filtro opcional por situação operacional."""
        stmt = select(ViaturaModel).order_by(ViaturaModel.prefixo)
        if situacoes:
            stmt = stmt.where(ViaturaModel.situacao.in_([s.value for s in situacoes]))
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._reconstituir(m) for m in models]
