"""
Adapter de saída: LaudoRepositorioSQLAlchemy (RF07 / UC07).

Implementação concreta de RepositorioLaudoPericial usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from adapters.outbound.persistence._concorrencia import RepositorioVersionadoSQLAlchemy
from adapters.outbound.persistence.mappers import LaudoMapper
from application.ports.outbound.repositorio_laudo import RepositorioLaudoPericial
from domain.laudo.entity import LaudoPericial, StatusLaudo
from infrastructure.database.models import LaudoPericialModel


class LaudoRepositorioSQLAlchemy(
    RepositorioVersionadoSQLAlchemy[LaudoPericialModel, LaudoPericial],
    RepositorioLaudoPericial,
):
    _model_cls = LaudoPericialModel
    _mapper_cls = LaudoMapper
    _mensagem_conflito = "O laudo pericial foi alterado por outro usuário; recarregue e tente novamente."

    async def buscar_por_referencia(self, numero_referencia: str) -> LaudoPericial | None:
        stmt = select(LaudoPericialModel).where(LaudoPericialModel.numero_referencia == numero_referencia)
        return self._reconstituir((await self._session.execute(stmt)).scalar_one_or_none())

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
        return [self._reconstituir(m) for m in models], total
