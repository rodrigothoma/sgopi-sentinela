"""
Adapter de saída: MedidaProtetivaRepositorioSQLAlchemy (RF09 / UC09).

Implementação concreta de RepositorioMedidaProtetiva usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._concorrencia import ControleVersaoMixin
from adapters.outbound.persistence.mappers import MedidaProtetivaMapper
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from infrastructure.database.models import MedidaProtetivaModel


class MedidaProtetivaRepositorioSQLAlchemy(ControleVersaoMixin, RepositorioMedidaProtetiva):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        super().__init__()

    async def _carregar_model(self, medida_id: UUID) -> MedidaProtetivaModel | None:
        stmt = select(MedidaProtetivaModel).where(MedidaProtetivaModel.id == medida_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def salvar(self, medida: MedidaProtetiva) -> None:
        existente = await self._carregar_model(medida.id)
        if existente is None:
            self._session.add(MedidaProtetivaMapper.to_model(medida))
        else:
            await self._verificar_versao(
                MedidaProtetivaModel,
                medida.id,
                medida.versao,
                "A medida protetiva foi alterada por outro usuário; recarregue e tente novamente.",
            )
            MedidaProtetivaMapper.atualizar_model(existente, medida)
        await self._session.flush()
        self._registrar_versao(medida.id, medida.versao)

    async def buscar_por_id(self, medida_id: UUID) -> MedidaProtetiva | None:
        model = await self._carregar_model(medida_id)
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return MedidaProtetivaMapper.to_domain(model)

    async def buscar_por_referencia(self, numero_referencia: str) -> MedidaProtetiva | None:
        stmt = select(MedidaProtetivaModel).where(MedidaProtetivaModel.numero_referencia == numero_referencia)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return MedidaProtetivaMapper.to_domain(model)

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
        for m in models:
            self._registrar_versao(m.id, m.versao)
        return [MedidaProtetivaMapper.to_domain(m) for m in models], total
