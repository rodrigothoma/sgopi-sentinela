"""
Adapter de saída: OcorrenciaRepositorioSQLAlchemy

Implementação concreta de RepositorioOcorrencia usando SQLAlchemy async.
Models SQLAlchemy são restritos à camada de adaptadores de persistência e seus mappers — nunca domain/ nem application/.

- Não confirma transação (papel da UnidadeDeTrabalho).
- Mapeamento e reconciliação delegados para OcorrenciaMapper (SRP).
- Optimistic locking via ``versao`` (RNF03): a versão carregada é rastreada por
  instância (uma por request); ao salvar, a linha é travada (``FOR UPDATE`` no
  Postgres) e comparada — divergência → ConflitoError (409).
"""
from __future__ import annotations

from datetime import UTC
from typing import Any
from uuid import UUID

from sqlalchemy import Select, case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from adapters.outbound.persistence._datas import aware
from adapters.outbound.persistence.mappers import OcorrenciaMapper
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import Ocorrencia
from domain.ocorrencia.prioridade import PrioridadeOcorrencia
from domain.shared.exceptions import ConflitoError
from infrastructure.database.models import ItemApreendidoModel, OcorrenciaModel

_ESCAPE: str = "\\"
# Ordenação por gravidade (URGENTE primeiro) sem depender da ordem alfabética do texto gravado
_PESO_PRIORIDADE = case({p.value: p.peso for p in PrioridadeOcorrencia}, value=OcorrenciaModel.prioridade, else_=0)


def _contendo(termo: str) -> str:
    """Gera padrão LIKE 'contém' com os curingas (% e _) tratados como literais."""
    literal = termo.replace(_ESCAPE, _ESCAPE * 2).replace("%", _ESCAPE + "%").replace("_", _ESCAPE + "_")
    return f"%{literal}%"


_CARREGAR_FILHOS = (
    selectinload(OcorrenciaModel.envolvidos),
    selectinload(OcorrenciaModel.tipificacoes),
    selectinload(OcorrenciaModel.historico),
    selectinload(OcorrenciaModel.evidencias),
    selectinload(OcorrenciaModel.itens_apreendidos).selectinload(ItemApreendidoModel.movimentacoes),
)


class OcorrenciaRepositorioSQLAlchemy(RepositorioOcorrencia):
    """Repositório de ocorrências com persistência relacional via SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._versoes_carregadas: dict[UUID, int] = {}

    async def _carregar_model(self, ocorrencia_id: UUID) -> OcorrenciaModel | None:
        stmt = select(OcorrenciaModel).where(OcorrenciaModel.id == ocorrencia_id).options(*_CARREGAR_FILHOS)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def _verificar_versao(self, ocorrencia: Ocorrencia) -> None:
        stmt = select(OcorrenciaModel.versao).where(OcorrenciaModel.id == ocorrencia.id).with_for_update()
        versao_banco = (await self._session.execute(stmt)).scalar_one()
        versao_esperada = self._versoes_carregadas.get(ocorrencia.id, versao_banco)
        if versao_banco != versao_esperada or ocorrencia.versao < versao_banco:
            raise ConflitoError(
                "A ocorrência foi alterada por outro usuário; recarregue e tente novamente.",
                chave="generic.versao_desatualizada",
                versao_atual=versao_banco,
            )

    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        """Persiste ocorrência com verificação de concorrência otimista (RNF03).

        Raises:
            ConflitoError: Se a ocorrência foi alterada por outro usuário no banco de dados.
        """
        existente = await self._carregar_model(ocorrencia.id)
        if existente is None:
            self._session.add(OcorrenciaMapper.to_model(ocorrencia))
        else:
            await self._verificar_versao(ocorrencia)
            OcorrenciaMapper.atualizar_model(existente, ocorrencia)
        await self._session.flush()
        self._versoes_carregadas[ocorrencia.id] = ocorrencia.versao

    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        """Localiza ocorrência pelo identificador primário com coleções filhas pré-carregadas."""
        model = await self._carregar_model(ocorrencia_id)
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return OcorrenciaMapper.to_domain(model)

    async def _buscar_primeira(self, stmt: Select[Any]) -> Ocorrencia | None:
        model = (await self._session.execute(stmt.options(*_CARREGAR_FILHOS))).scalars().first()
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
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

    def _aplicar_filtro(self, stmt: Select[Any], filtro: FiltroOcorrencias) -> Select[Any]:
        if filtro.status:
            stmt = stmt.where(OcorrenciaModel.status.in_([s.value for s in filtro.status]))
        if filtro.agente_policial_id:
            stmt = stmt.where(OcorrenciaModel.agente_policial_id == filtro.agente_policial_id)
        return self._aplicar_busca(stmt, filtro)

    @staticmethod
    def _aplicar_busca(stmt: Select[Any], filtro: FiltroOcorrencias) -> Select[Any]:
        """Aplica filtros de busca textual com ILIKE portável e intervalos temporais em UTC."""
        if filtro.natureza:
            stmt = stmt.where(OcorrenciaModel.natureza.ilike(_contendo(filtro.natureza), escape=_ESCAPE))
        if filtro.protocolo:
            stmt = stmt.where(OcorrenciaModel.numero_protocolo.ilike(_contendo(filtro.protocolo), escape=_ESCAPE))
        if filtro.texto:
            padrao = _contendo(filtro.texto)
            stmt = stmt.where(
                or_(
                    OcorrenciaModel.descricao.ilike(padrao, escape=_ESCAPE),
                    OcorrenciaModel.localizacao.ilike(padrao, escape=_ESCAPE),
                )
            )
        if filtro.origem:
            stmt = stmt.where(OcorrenciaModel.origem == filtro.origem.value)
        if filtro.data_fato_de:
            stmt = stmt.where(OcorrenciaModel.data_hora_fato >= aware(filtro.data_fato_de).astimezone(UTC))
        if filtro.data_fato_ate:
            stmt = stmt.where(OcorrenciaModel.data_hora_fato <= aware(filtro.data_fato_ate).astimezone(UTC))
        return stmt

    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        """Lista ocorrências paginadas conforme filtros e prioridade de atendimento."""
        stmt = self._aplicar_filtro(select(OcorrenciaModel), filtro)
        ordem = OcorrenciaModel.criada_em.desc() if filtro.mais_recentes_primeiro else OcorrenciaModel.criada_em.asc()
        criterios = (_PESO_PRIORIDADE.desc(), ordem) if filtro.ordenar_por_prioridade else (ordem,)
        stmt = stmt.options(*_CARREGAR_FILHOS).order_by(*criterios).limit(filtro.limit).offset(filtro.offset)
        models = (await self._session.execute(stmt)).scalars().all()
        for m in models:
            self._versoes_carregadas[m.id] = m.versao
        return [OcorrenciaMapper.to_domain(m) for m in models]

    async def contar(self, filtro: FiltroOcorrencias) -> int:
        """Totaliza as ocorrências que atendem aos filtros fornecidos sem limites de paginação."""
        stmt = self._aplicar_filtro(select(func.count(OcorrenciaModel.id)), filtro)
        return int((await self._session.execute(stmt)).scalar_one())

    async def lacre_em_uso(self, numero_lacre: str) -> bool:
        """Garante a unicidade global do número de lacre de apreensão em toda a base (RF03/UC03)."""
        stmt = select(exists().where(ItemApreendidoModel.numero_lacre == numero_lacre))
        return bool((await self._session.execute(stmt)).scalar_one())
