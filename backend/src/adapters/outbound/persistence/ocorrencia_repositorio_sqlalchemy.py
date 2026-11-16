"""
Adapter de saída: OcorrenciaRepositorioSQLAlchemy

Implementação concreta de RepositorioOcorrencia usando SQLAlchemy async.
Models SQLAlchemy são restritos à camada de adaptadores de persistência e seus mappers — nunca domain/ nem application/.

- Não confirma transação (papel da UnidadeDeTrabalho).
- Mapeamento e reconciliação delegados para OcorrenciaMapper (SRP).
- Construção de queries e filtros complexos delegados para OcorrenciaQueryBuilder (SRP).
- Optimistic locking via ControleVersaoMixin (RNF03).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._concorrencia import ControleVersaoMixin
from adapters.outbound.persistence._ocorrencia_queries import CARREGAR_FILHOS, OcorrenciaQueryBuilder
from adapters.outbound.persistence.mappers import OcorrenciaMapper
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import Ocorrencia
from infrastructure.database.models import ItemApreendidoModel, OcorrenciaModel


class OcorrenciaRepositorioSQLAlchemy(ControleVersaoMixin, RepositorioOcorrencia):
    """Repositório de ocorrências com persistência relacional via SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        super().__init__()

    async def _carregar_model(self, ocorrencia_id: UUID) -> OcorrenciaModel | None:
        stmt = select(OcorrenciaModel).where(OcorrenciaModel.id == ocorrencia_id).options(*CARREGAR_FILHOS)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        """Persiste ocorrência com verificação de concorrência otimista (RNF03).

        Raises:
            ConflitoError: Se a ocorrência foi alterada por outro usuário no banco de dados.
        """
        existente = await self._carregar_model(ocorrencia.id)
        if existente is None:
            self._session.add(OcorrenciaMapper.to_model(ocorrencia))
        else:
            await self._verificar_versao(
                OcorrenciaModel,
                ocorrencia.id,
                ocorrencia.versao,
                "A ocorrência foi alterada por outro usuário; recarregue e tente novamente.",
            )
            OcorrenciaMapper.atualizar_model(existente, ocorrencia)
        await self._session.flush()
        self._registrar_versao(ocorrencia.id, ocorrencia.versao)

    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        """Localiza ocorrência pelo identificador primário com coleções filhas pré-carregadas."""
        model = await self._carregar_model(ocorrencia_id)
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return OcorrenciaMapper.to_domain(model)

    async def _buscar_primeira(self, stmt: Select[Any]) -> Ocorrencia | None:
        model = (await self._session.execute(stmt.options(*CARREGAR_FILHOS))).scalars().first()
        if model is None:
            return None
        self._registrar_versao(model.id, model.versao)
        return OcorrenciaMapper.to_domain(model)

    async def buscar_por_protocolo(self, numero_protocolo: str) -> Ocorrencia | None:
        """Localiza a ocorrência pelo número de protocolo público oficial (RF01/UC01)."""
        return await self._buscar_primeira(select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == numero_protocolo))

    async def buscar_por_chave_autenticidade(self, chave: str) -> Ocorrencia | None:
        """Localiza o documento emitido pela chave de segurança pública (RF08)."""
        return await self._buscar_primeira(select(OcorrenciaModel).where(OcorrenciaModel.chave_autenticidade == chave))

    async def buscar_por_hash_narrativa(self, hash_narrativa: str) -> Ocorrencia | None:
        """Localiza a ocorrência pelo hash SHA-256 de integridade da narrativa impressa (RF08)."""
        stmt = (
            select(OcorrenciaModel)
            .where(OcorrenciaModel.hash_narrativa == hash_narrativa)
            .order_by(OcorrenciaModel.criada_em.asc())
        )
        return await self._buscar_primeira(stmt)

    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        """Lista ocorrências paginadas conforme filtros e prioridade de atendimento."""
        stmt = OcorrenciaQueryBuilder.construir_listagem(filtro)
        models = (await self._session.execute(stmt)).scalars().all()
        for m in models:
            self._registrar_versao(m.id, m.versao)
        return [OcorrenciaMapper.to_domain(m) for m in models]

    async def contar(self, filtro: FiltroOcorrencias) -> int:
        """Totaliza as ocorrências que atendem aos filtros fornecidos sem limites de paginação."""
        stmt = OcorrenciaQueryBuilder.construir_contagem(filtro)
        return int((await self._session.execute(stmt)).scalar_one())

    async def lacre_em_uso(self, numero_lacre: str) -> bool:
        """Garante a unicidade global do número de lacre de apreensão em toda a base (RF03/UC03)."""
        stmt = select(exists().where(ItemApreendidoModel.numero_lacre == numero_lacre))
        return bool((await self._session.execute(stmt)).scalar_one())
