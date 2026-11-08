"""Adapter de saída: ViaturaRepositorioSQLAlchemy (RF02) com optimistic locking por ``versao``."""
from __future__ import annotations

from typing import overload
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence.mappers import ViaturaMapper
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from domain.shared.exceptions import ConflitoError
from domain.viatura.entity import SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel


class ViaturaRepositorioSQLAlchemy(RepositorioViatura):
    """Repositório de viaturas policiais com persistência relacional via SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._versoes_carregadas: dict[UUID, int] = {}

    @overload
    def _reconstituir(self, model: None) -> None: ...

    @overload
    def _reconstituir(self, model: ViaturaModel) -> Viatura: ...

    def _reconstituir(self, model: ViaturaModel | None) -> Viatura | None:
        """Registra a versão atual para controle otimista e converte o model para entidade."""
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
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
            stmt = select(ViaturaModel.versao).where(ViaturaModel.id == viatura.id).with_for_update()
            versao_banco = (await self._session.execute(stmt)).scalar_one()
            esperada = self._versoes_carregadas.get(viatura.id, versao_banco)
            if versao_banco != esperada or viatura.versao < versao_banco:
                raise ConflitoError("A viatura foi alterada por outro usuário.", chave="generic.versao_desatualizada", versao_atual=versao_banco)
            ViaturaMapper.atualizar_model(model, viatura)

        await self._session.flush()
        self._versoes_carregadas[viatura.id] = viatura.versao

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
