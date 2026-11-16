"""
Adapter de saída: LaudoRepositorioSQLAlchemy (RF07 / UC07).

Implementação concreta de RepositorioLaudoPericial usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._concorrencia import ControleVersaoMixin
from adapters.outbound.persistence.mappers import LaudoMapper
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from domain.laudo.entity import LaudoPericial, StatusLaudo
from infrastructure.database.models import LaudoPericialModel


class LaudoRepositorioSQLAlchemy(ControleVersaoMixin, RepositorioLaudoPericial):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        super().__init__()

    async def _carregar_model(self, laudo_id: UUID) -> LaudoPericialModel | None:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.id == laudo_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def salvar(self, laudo: LaudoPericial) -> None:
        existente = await self._carregar_model(laudo.id)
        if existente is None:
            self._session.add(LaudoMapper.to_model(laudo))
        else:
            await self._verificar_versao(
                LaudoPericialModel,
                laudo.id,
                laudo.versao,
                "O laudo pericial foi alterado por outro usuário; recarregue e tente novamente.",
            )
            LaudoMapper.atualizar_model(existente, laudo)
        await self._session.flush()
        self._registrar_versao(laudo.id, laudo.versao)

    async def buscar_por_id(self, laudo_id: UUID) -> LaudoPericial | None:
        model = await self._carregar_model(laudo_id)
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return LaudoMapper.to_domain(model)

    async def buscar_por_referencia(self, numero_referencia: str) -> LaudoPericial | None:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.numero_referencia == numero_referencia)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return LaudoMapper.to_domain(model)

    async def listar(
        self,
        status: list[StatusLaudo] | None = None,
        ocorrencia_id: UUID | None = None,
        inquerito_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LaudoPericial], int]:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.ativo.is_(True))
        if status:
            stmt = stmt.where(LaudoPericialModel.status.in_([s.value for s in status]))
        if ocorrencia_id:
            stmt = stmt.where(LaudoPericialModel.ocorrencia_id == ocorrencia_id)
        if inquerito_id:
            stmt = stmt.where(LaudoPericialModel.inquerito_id == inquerito_id)

        total = (await self._session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = stmt.order_by(LaudoPericialModel.solicitado_em.desc()).offset(offset).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        for m in models:
            self._registrar_versao(m.id, m.versao)
        return [LaudoMapper.to_domain(m) for m in models], total
