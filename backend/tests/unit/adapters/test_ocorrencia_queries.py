"""Testes unitários do builder de consultas e filtros de ocorrência (RF01/UC01)."""
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Select
from sqlalchemy.dialects import sqlite

from adapters.outbound.persistence._ocorrencia_queries import OcorrenciaQueryBuilder, _contendo
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias
from domain.ocorrencia.entity import OrigemOcorrencia, StatusOcorrencia


def _sql(stmt: Select[Any]) -> str:
    """Compila a cláusula SQLAlchemy para string SQL usando dialeto SQLite."""
    return str(stmt.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}))


def test_contendo_escapa_caracteres_especiais() -> None:
    termo = "100%_teste\\seguro"
    padrao = _contendo(termo)
    assert padrao == "%100\\%\\_teste\\\\seguro%"


def test_construir_listagem_com_filtros_basicos() -> None:
    agente_id = uuid4()
    filtro = FiltroOcorrencias(
        status=(StatusOcorrencia.AGUARDANDO_REVISAO, StatusOcorrencia.VALIDADA),
        agente_policial_id=agente_id,
        natureza="Furto",
        protocolo="SGOPI-2026",
        limit=20,
        offset=40,
    )

    stmt = OcorrenciaQueryBuilder.construir_listagem(filtro)
    sql = _sql(stmt)

    assert "ocorrencias.agente_policial_id =" in sql
    assert "ocorrencias.status IN ('AGUARDANDO_REVISAO', 'VALIDADA')" in sql
    assert "ocorrencias.natureza) LIKE" in sql
    assert "ocorrencias.numero_protocolo) LIKE" in sql
    assert "LIMIT 20 OFFSET 40" in sql


def test_construir_listagem_com_busca_textual_e_datas() -> None:
    dt_inicio = datetime(2026, 11, 1, 10, 0)
    dt_fim = datetime(2026, 11, 8, 20, 0, tzinfo=UTC)

    filtro = FiltroOcorrencias(
        texto="Av. Brasil",
        origem=OrigemOcorrencia.POLICIAL,
        data_fato_de=dt_inicio,
        data_fato_ate=dt_fim,
    )

    stmt = OcorrenciaQueryBuilder.construir_listagem(filtro)
    sql = _sql(stmt)

    assert "ocorrencias.descricao) LIKE" in sql
    assert "ocorrencias.localizacao) LIKE" in sql
    assert "ocorrencias.origem = 'POLICIAL'" in sql
    assert "ocorrencias.data_hora_fato >= '2026-11-01 10:00:00" in sql
    assert "ocorrencias.data_hora_fato <= '2026-11-08 20:00:00" in sql


def test_construir_listagem_ordenacao_por_prioridade_e_data() -> None:
    filtro = FiltroOcorrencias(
        ordenar_por_prioridade=True,
        mais_recentes_primeiro=False,
    )

    stmt = OcorrenciaQueryBuilder.construir_listagem(filtro)
    sql = _sql(stmt)

    # Deve conter CASE da prioridade e ordenação ascendente por criada_em
    assert "CASE ocorrencias.prioridade" in sql
    assert "DESC, ocorrencias.criada_em ASC" in sql


def test_construir_contagem() -> None:
    filtro = FiltroOcorrencias(status=(StatusOcorrencia.VALIDADA,))

    stmt = OcorrenciaQueryBuilder.construir_contagem(filtro)
    sql = _sql(stmt)

    assert "count(ocorrencias.id)" in sql
    assert "ocorrencias.status IN ('VALIDADA')" in sql
    assert "LIMIT" not in sql
