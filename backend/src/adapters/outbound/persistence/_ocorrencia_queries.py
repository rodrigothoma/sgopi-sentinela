"""Construção de queries e filtros para consulta de ocorrências (RF01/UC01)."""
from __future__ import annotations

from datetime import UTC
from typing import Any

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import selectinload

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias
from domain.ocorrencia.prioridade import PrioridadeOcorrencia
from infrastructure.database.models import ItemApreendidoModel, OcorrenciaModel

_ESCAPE: str = "\\"

# Ordenação por gravidade (URGENTE primeiro) sem depender da ordem alfabética do texto gravado
_PESO_PRIORIDADE = case(
    {p.value: p.peso for p in PrioridadeOcorrencia},
    value=OcorrenciaModel.prioridade,
    else_=0,
)

CARREGAR_FILHOS = (
    selectinload(OcorrenciaModel.envolvidos),
    selectinload(OcorrenciaModel.tipificacoes),
    selectinload(OcorrenciaModel.historico),
    selectinload(OcorrenciaModel.evidencias),
    selectinload(OcorrenciaModel.itens_apreendidos).selectinload(ItemApreendidoModel.movimentacoes),
)


def _contendo(termo: str) -> str:
    """Gera padrão LIKE 'contém' com os curingas (% e _) tratados como literais."""
    literal = termo.replace(_ESCAPE, _ESCAPE * 2).replace("%", _ESCAPE + "%").replace("_", _ESCAPE + "_")
    return f"%{literal}%"


class OcorrenciaQueryBuilder:
    """Builder de consultas SQLAlchemy para listagem e contagem de ocorrências."""

    @staticmethod
    def filtrar(stmt: Select[Any], filtro: FiltroOcorrencias) -> Select[Any]:
        """Aplica filtros textuais, temporais e de estado sobre a query base."""
        if filtro.status:
            stmt = stmt.where(OcorrenciaModel.status.in_([s.value for s in filtro.status]))
        if filtro.agente_policial_id:
            stmt = stmt.where(OcorrenciaModel.agente_policial_id == filtro.agente_policial_id)
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

    @classmethod
    def construir_listagem(cls, filtro: FiltroOcorrencias) -> Select[tuple[OcorrenciaModel]]:
        """Monta a query completa de listagem com filtros, opções de carregamento, ordenação e paginação."""
        stmt = cls.filtrar(select(OcorrenciaModel), filtro)
        ordem = OcorrenciaModel.criada_em.desc() if filtro.mais_recentes_primeiro else OcorrenciaModel.criada_em.asc()
        criterios = (_PESO_PRIORIDADE.desc(), ordem) if filtro.ordenar_por_prioridade else (ordem,)
        return stmt.options(*CARREGAR_FILHOS).order_by(*criterios).limit(filtro.limit).offset(filtro.offset)

    @classmethod
    def construir_contagem(cls, filtro: FiltroOcorrencias) -> Select[tuple[int]]:
        """Monta a query de contagem de registros que atendem ao filtro."""
        return cls.filtrar(select(func.count(OcorrenciaModel.id)), filtro)
