"""
Adapter de saída: MedidaProtetivaRepositorioSQLAlchemy (RF09 / UC09).

Implementação concreta de RepositorioMedidaProtetiva usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from adapters.outbound.persistence._concorrencia import RepositorioVersionadoSQLAlchemy
from adapters.outbound.persistence.mappers import MedidaProtetivaMapper
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from infrastructure.database.models import MedidaProtetivaModel


class MedidaProtetivaRepositorioSQLAlchemy(
    RepositorioVersionadoSQLAlchemy[MedidaProtetivaModel, MedidaProtetiva],
    RepositorioMedidaProtetiva,
):
    _model_cls = MedidaProtetivaModel
    _mapper_cls = MedidaProtetivaMapper
    _mensagem_conflito = "A medida protetiva foi alterada por outro usuário; recarregue e tente novamente."

    async def buscar_por_referencia(self, numero_referencia: str) -> MedidaProtetiva | None:
        stmt = select(MedidaProtetivaModel).where(MedidaProtetivaModel.numero_referencia == numero_referencia)
        return self._reconstituir((await self._session.execute(stmt)).scalar_one_or_none())

    async def listar(
        self,
        status: list[StatusMedida] | None = None,
        ocorrencia_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MedidaProtetiva], int]:
        stmt = select(MedidaProtetivaModel).where(MedidaProtetivaModel.ativo.is_(True))
        if status:
            stmt = stmt.where(MedidaProtetivaModel.status.in_([s.value for s in status]))
        if ocorrencia_id:
            stmt = stmt.where(MedidaProtetivaModel.ocorrencia_id == ocorrencia_id)

        total = (await self._session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        stmt = stmt.order_by(MedidaProtetivaModel.criada_em.desc()).offset(offset).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._reconstituir(m) for m in models], total
