"""
Adapter de saída: MedidaProtetivaRepositorioSQLAlchemy (RF09 / UC09).

Implementação concreta de RepositorioMedidaProtetiva usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from domain.shared.exceptions import ConflitoError
from infrastructure.database.models import MedidaProtetivaModel


class MedidaProtetivaRepositorioSQLAlchemy(RepositorioMedidaProtetiva):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._versoes_carregadas: dict[UUID, int] = {}

    async def _carregar_model(self, medida_id: UUID) -> MedidaProtetivaModel | None:
        stmt = select(MedidaProtetivaModel).where(MedidaProtetivaModel.id == medida_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _verificar_versao(self, medida: MedidaProtetiva) -> None:
        stmt = select(MedidaProtetivaModel.versao).where(MedidaProtetivaModel.id == medida.id).with_for_update()
        versao_banco = (await self._session.execute(stmt)).scalar_one()
        versao_esperada = self._versoes_carregadas.get(medida.id, versao_banco)
        if versao_banco != versao_esperada or medida.versao < versao_banco:
            raise ConflitoError(
                "A medida protetiva foi alterada por outro usuário; recarregue e tente novamente.",
                chave="generic.versao_desatualizada",
                versao_atual=versao_banco,
            )

    async def salvar(self, medida: MedidaProtetiva) -> None:
        existente = await self._carregar_model(medida.id)
        if existente is None:
            model = MedidaProtetivaModel(
                id=medida.id,
                numero_referencia=medida.numero_referencia,
                ocorrencia_id=medida.ocorrencia_id,
                delegado_id=medida.delegado_id,
                vitima_id=medida.vitima_id,
                agressor_id=medida.agressor_id,
                tipos_restricao=medida.tipos_restricao,
                distancia_minima_metros=medida.distancia_minima_metros,
                data_inicio=medida.data_inicio,
                prazo_dias=medida.prazo_dias,
                data_vencimento=medida.data_vencimento,
                condicoes_especificas=medida.condicoes_especificas,
                motivo_revogacao=medida.motivo_revogacao,
                justificativa_renovacao=medida.justificativa_renovacao,
                status=medida.status.value,
                criada_em=medida.criada_em,
                atualizada_em=medida.atualizada_em,
                ativo=medida.ativo,
                versao=medida.versao,
            )
            self._session.add(model)
        else:
            await self._verificar_versao(medida)
            existente.tipos_restricao = medida.tipos_restricao
            existente.distancia_minima_metros = medida.distancia_minima_metros
            existente.prazo_dias = medida.prazo_dias
            existente.data_vencimento = medida.data_vencimento
            existente.condicoes_especificas = medida.condicoes_especificas
            existente.motivo_revogacao = medida.motivo_revogacao
            existente.justificativa_renovacao = medida.justificativa_renovacao
            existente.status = medida.status.value
            existente.atualizada_em = medida.atualizada_em
            existente.ativo = medida.ativo
            existente.versao = medida.versao
        await self._session.flush()
        self._versoes_carregadas[medida.id] = medida.versao

    async def buscar_por_id(self, medida_id: UUID) -> MedidaProtetiva | None:
        model = await self._carregar_model(medida_id)
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

    async def buscar_por_referencia(self, numero_referencia: str) -> MedidaProtetiva | None:
        stmt = select(MedidaProtetivaModel).where(MedidaProtetivaModel.numero_referencia == numero_referencia)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

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
            self._versoes_carregadas[m.id] = m.versao
        return [self._to_domain(m) for m in models], total

    @staticmethod
    def _to_domain(model: MedidaProtetivaModel) -> MedidaProtetiva:
        return MedidaProtetiva(
            id=model.id,
            numero_referencia=model.numero_referencia,
            ocorrencia_id=model.ocorrencia_id,
            delegado_id=model.delegado_id,
            vitima_id=model.vitima_id,
            agressor_id=model.agressor_id,
            tipos_restricao=list(model.tipos_restricao),
            distancia_minima_metros=model.distancia_minima_metros,
            data_inicio=model.data_inicio,
            prazo_dias=model.prazo_dias,
            data_vencimento=model.data_vencimento,
            condicoes_especificas=model.condicoes_especificas,
            motivo_revogacao=model.motivo_revogacao,
            justificativa_renovacao=model.justificativa_renovacao,
            status=StatusMedida(model.status),
            criada_em=aware(model.criada_em),
            atualizada_em=aware(model.atualizada_em) if model.atualizada_em else None,
            ativo=model.ativo,
            versao=model.versao,
        )
