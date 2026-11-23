"""
Adapter de saída: OcorrenciaRepositorioSQLAlchemy

Implementação concreta de RepositorioOcorrencia usando SQLAlchemy async.
Models SQLAlchemy são restritos à camada de adaptadores de persistência e seus mappers — nunca domain/ nem application/.

- Não confirma transação (papel da UnidadeDeTrabalho).
- Mapeamento e reconciliação delegados para OcorrenciaMapper (SRP).
- Construção de queries e filtros complexos delegados para OcorrenciaQueryBuilder (SRP).
- salvar/buscar_por_id e optimistic locking herdados de RepositorioVersionadoSQLAlchemy (RNF03).
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, exists, select

from adapters.outbound.persistence._concorrencia import RepositorioVersionadoSQLAlchemy
from adapters.outbound.persistence._ocorrencia_queries import CARREGAR_FILHOS, OcorrenciaQueryBuilder
from adapters.outbound.persistence.mappers import OcorrenciaMapper
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import Ocorrencia
from infrastructure.database.models import ItemApreendidoModel, OcorrenciaModel


class OcorrenciaRepositorioSQLAlchemy(
    RepositorioVersionadoSQLAlchemy[OcorrenciaModel, Ocorrencia],
    RepositorioOcorrencia,
):
    """Repositório de ocorrências com persistência relacional via SQLAlchemy async."""

    _model_cls = OcorrenciaModel
    _mapper_cls = OcorrenciaMapper
    _mensagem_conflito = "A ocorrência foi alterada por outro usuário; recarregue e tente novamente."

    def _query_carregar_model(self, entidade_id: UUID) -> Select[tuple[OcorrenciaModel]]:
        return super()._query_carregar_model(entidade_id).options(*CARREGAR_FILHOS)

    async def _buscar_primeira(self, stmt: Select[tuple[OcorrenciaModel]]) -> Ocorrencia | None:
        return self._reconstituir((await self._session.execute(stmt.options(*CARREGAR_FILHOS))).scalars().first())

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
        return [self._reconstituir(m) for m in models]

    async def contar(self, filtro: FiltroOcorrencias) -> int:
        """Totaliza as ocorrências que atendem aos filtros fornecidos sem limites de paginação."""
        stmt = OcorrenciaQueryBuilder.construir_contagem(filtro)
        return int((await self._session.execute(stmt)).scalar_one())

    async def lacre_em_uso(self, numero_lacre: str) -> bool:
        """Garante a unicidade global do número de lacre de apreensão em toda a base (RF03/UC03)."""
        stmt = select(exists().where(ItemApreendidoModel.numero_lacre == numero_lacre))
        return bool((await self._session.execute(stmt)).scalar_one())
