"""
Adapter de saída: InqueritoRepositorioSQLAlchemy (RF06 / UC06).

Implementação concreta de RepositorioInquerito usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from adapters.outbound.persistence._concorrencia import RepositorioVersionadoSQLAlchemy
from adapters.outbound.persistence.mappers import InqueritoMapper
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from domain.inquerito.entity import Inquerito, StatusInquerito
from infrastructure.database.models import InqueritoModel

_CARREGAR_OCORRENCIAS = selectinload(InqueritoModel.ocorrencias)


class InqueritoRepositorioSQLAlchemy(
    RepositorioVersionadoSQLAlchemy[InqueritoModel, Inquerito],
    RepositorioInquerito,
):
    _model_cls = InqueritoModel
    _mapper_cls = InqueritoMapper
    _mensagem_conflito = "O inquérito foi alterado por outro usuário; recarregue e tente novamente."

    def _query_carregar_model(self, entidade_id: UUID) -> Select[tuple[InqueritoModel]]:
        return super()._query_carregar_model(entidade_id).options(_CARREGAR_OCORRENCIAS)

    async def buscar_por_numero(self, numero: str) -> Inquerito | None:
        stmt = select(InqueritoModel).where(InqueritoModel.numero == numero).options(_CARREGAR_OCORRENCIAS)
        return self._reconstituir((await self._session.execute(stmt)).scalar_one_or_none())

    async def listar(
        self,
        status: list[StatusInquerito] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Inquerito], int]:
        stmt = select(InqueritoModel).where(InqueritoModel.ativo.is_(True))
        if status:
            stmt = stmt.where(InqueritoModel.status.in_([s.value for s in status]))

        total = (await self._session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = (
            stmt.options(_CARREGAR_OCORRENCIAS)
            .order_by(InqueritoModel.data_abertura.desc())
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._reconstituir(m) for m in models], total
