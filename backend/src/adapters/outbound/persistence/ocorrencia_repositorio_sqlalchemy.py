"""
Adapter de saída: OcorrenciaRepositorioSQLAlchemy

Implementação concreta de RepositorioOcorrencia usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from domain.ocorrencia.entity import (
    Envolvido,
    Ocorrencia,
    StatusOcorrencia,
    TipificacaoPenal,
    TipoEnvolvido,
)
from infrastructure.database.models import EnvolvidoModel, OcorrenciaModel, TipificacaoModel


class OcorrenciaRepositorioSQLAlchemy(RepositorioOcorrencia):
    """Repositório de ocorrências com persistência em PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        model = self._to_model(ocorrencia)
        await self._session.merge(model)
        await self._session.commit()

    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        stmt = (
            select(OcorrenciaModel)
            .where(OcorrenciaModel.id == ocorrencia_id)
            .options(
                selectinload(OcorrenciaModel.envolvidos),
                selectinload(OcorrenciaModel.tipificacoes),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def listar(self, status: str | None = None) -> list[Ocorrencia]:
        stmt = select(OcorrenciaModel).options(
            selectinload(OcorrenciaModel.envolvidos),
            selectinload(OcorrenciaModel.tipificacoes),
        )
        if status:
            stmt = stmt.where(OcorrenciaModel.status == status)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]


    def _to_model(self, ocorrencia: Ocorrencia) -> OcorrenciaModel:
        model = OcorrenciaModel(
            id=ocorrencia.id,
            agente_policial_id=ocorrencia.agente_policial_id,
            natureza=ocorrencia.natureza,
            descricao=ocorrencia.descricao,
            localizacao=ocorrencia.localizacao,
            numero_protocolo=ocorrencia.numero_protocolo,
            status=ocorrencia.status.value,
            criada_em=ocorrencia.criada_em,
            validada_por_id=ocorrencia.validada_por_id,
        )
        model.envolvidos = [
            EnvolvidoModel(id=e.id, nome=e.nome, tipo=e.tipo.value, documento=e.documento)
            for e in ocorrencia.envolvidos
        ]
        model.tipificacoes = [
            TipificacaoModel(artigo=t.artigo, descricao=t.descricao)
            for t in ocorrencia.tipificacoes
        ]
        return model

    def _to_domain(self, model: OcorrenciaModel) -> Ocorrencia:
        ocorrencia = Ocorrencia(
            id=model.id,
            agente_policial_id=model.agente_policial_id,
            natureza=model.natureza,
            descricao=model.descricao,
            localizacao=model.localizacao,
            numero_protocolo=model.numero_protocolo,
            status=StatusOcorrencia(model.status),
            criada_em=model.criada_em,
            validada_por_id=model.validada_por_id,
        )
        ocorrencia.envolvidos = [
            Envolvido(id=e.id, nome=e.nome, tipo=TipoEnvolvido(e.tipo), documento=e.documento)
            for e in model.envolvidos
        ]
        ocorrencia.tipificacoes = [
            TipificacaoPenal(artigo=t.artigo, descricao=t.descricao)
            for t in model.tipificacoes
        ]
        return ocorrencia
