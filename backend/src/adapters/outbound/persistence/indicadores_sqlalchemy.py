"""
Adapter de saída: ConsultaIndicadores com SQLAlchemy (sugestão #11).

Toda agregação roda no banco (GROUP BY / AVG / COUNT). Diferença entre instantes e hora do dia
não são portáveis, então as duas expressões são montadas por dialeto: PostgreSQL usa
``EXTRACT(EPOCH ...)``/``EXTRACT(HOUR ...)`` em UTC; SQLite usa ``julianday``/``strftime`` (datas
gravadas em UTC, sem fuso).
"""
from datetime import UTC, datetime

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement, Select

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.consulta_indicadores import ConsultaIndicadores, MediaDuracao
from domain.ocorrencia.status import StatusOcorrencia
from infrastructure.database.models import HistoricoStatusModel, OcorrenciaModel, OrdemDespachoModel, ViaturaModel

SEGUNDOS_POR_DIA = 86400.0
_DECISOES = (StatusOcorrencia.VALIDADA.value, StatusOcorrencia.EM_CORRECAO.value, StatusOcorrencia.REJEITADA.value)


def _utc(instante: datetime) -> datetime:
    return aware(instante).astimezone(UTC)


class IndicadoresSQLAlchemy(ConsultaIndicadores):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------ dialeto
    @property
    def _postgres(self) -> bool:
        return self._session.bind.dialect.name == "postgresql"

    def _segundos_entre(self, inicio: ColumnElement, fim: ColumnElement) -> ColumnElement:
        if self._postgres:
            return func.extract("epoch", fim - inicio)
        return (func.julianday(fim) - func.julianday(inicio)) * SEGUNDOS_POR_DIA

    def _hora_utc(self, coluna: ColumnElement) -> ColumnElement:
        if self._postgres:
            return cast(func.extract("hour", func.timezone("UTC", coluna)), Integer)
        return cast(func.strftime("%H", coluna), Integer)

    # ------------------------------------------------------------ apoio
    async def _contagem(self, stmt: Select) -> dict:
        return {chave: int(total) for chave, total in (await self._session.execute(stmt)).all()}

    async def _media(self, stmt: Select) -> MediaDuracao:
        media, amostras = (await self._session.execute(stmt)).one()
        return MediaDuracao(segundos=float(media) if media is not None else None, amostras=int(amostras or 0))

    def _ocorrencias_do_periodo(self, stmt: Select, de: datetime, ate: datetime) -> Select:
        return stmt.where(
            OcorrenciaModel.criada_em.between(_utc(de), _utc(ate)),
            OcorrenciaModel.status != StatusOcorrencia.EXCLUIDA.value,
        )

    @staticmethod
    def _primeira_transicao(para: str, *, de: str | None = None):
        stmt = select(HistoricoStatusModel.ocorrencia_id, func.min(HistoricoStatusModel.em).label("em"))
        stmt = stmt.where(HistoricoStatusModel.para == para)
        if de is not None:
            stmt = stmt.where(HistoricoStatusModel.de == de)
        return stmt.group_by(HistoricoStatusModel.ocorrencia_id).subquery()

    @staticmethod
    def _primeiro_despacho():
        return (
            select(OrdemDespachoModel.ocorrencia_id, func.min(OrdemDespachoModel.criada_em).label("em"))
            .group_by(OrdemDespachoModel.ocorrencia_id)
            .subquery()
        )

    # ------------------------------------------------------------ RF01
    async def ocorrencias_por_natureza(self, de: datetime, ate: datetime) -> dict[str, int]:
        stmt = select(OcorrenciaModel.natureza, func.count()).group_by(OcorrenciaModel.natureza)
        return await self._contagem(self._ocorrencias_do_periodo(stmt, de, ate))

    async def ocorrencias_por_origem(self, de: datetime, ate: datetime) -> dict[str, int]:
        stmt = select(OcorrenciaModel.origem, func.count()).group_by(OcorrenciaModel.origem)
        return await self._contagem(self._ocorrencias_do_periodo(stmt, de, ate))

    async def ocorrencias_por_hora_utc(self, de: datetime, ate: datetime) -> dict[int, int]:
        hora = self._hora_utc(OcorrenciaModel.data_hora_fato).label("hora")
        stmt = select(hora, func.count()).group_by(hora)
        return await self._contagem(self._ocorrencias_do_periodo(stmt, de, ate))

    # ------------------------------------------------------------ RF04
    async def decisoes_do_delegado(self, de: datetime, ate: datetime) -> dict[str, int]:
        stmt = (
            select(HistoricoStatusModel.para, func.count())
            .where(
                HistoricoStatusModel.de == StatusOcorrencia.AGUARDANDO_REVISAO.value,
                HistoricoStatusModel.para.in_(_DECISOES),
                HistoricoStatusModel.em.between(_utc(de), _utc(ate)),
            )
            .group_by(HistoricoStatusModel.para)
        )
        return await self._contagem(stmt)

    async def tempo_ate_primeira_decisao(self, de: datetime, ate: datetime) -> MediaDuracao:
        decisao = (
            select(HistoricoStatusModel.ocorrencia_id, func.min(HistoricoStatusModel.em).label("em"))
            .where(
                HistoricoStatusModel.de == StatusOcorrencia.AGUARDANDO_REVISAO.value,
                HistoricoStatusModel.para.in_(_DECISOES),
            )
            .group_by(HistoricoStatusModel.ocorrencia_id)
            .subquery()
        )
        duracao = self._segundos_entre(OcorrenciaModel.criada_em, decisao.c.em)
        stmt = (
            select(func.avg(duracao), func.count())
            .select_from(OcorrenciaModel)
            .join(decisao, decisao.c.ocorrencia_id == OcorrenciaModel.id)
            .where(decisao.c.em.between(_utc(de), _utc(ate)))
        )
        return await self._media(stmt)

    # ------------------------------------------------------------ RF02
    async def tempo_validacao_ate_despacho(self, de: datetime, ate: datetime) -> MediaDuracao:
        validacao = self._primeira_transicao(StatusOcorrencia.VALIDADA.value)
        despacho = self._primeiro_despacho()
        stmt = (
            select(func.avg(self._segundos_entre(validacao.c.em, despacho.c.em)), func.count())
            .select_from(validacao)
            .join(despacho, despacho.c.ocorrencia_id == validacao.c.ocorrencia_id)
            .where(despacho.c.em.between(_utc(de), _utc(ate)))
        )
        return await self._media(stmt)

    async def tempo_despacho_ate_encerramento(self, de: datetime, ate: datetime) -> MediaDuracao:
        despacho = self._primeiro_despacho()
        encerramento = self._primeira_transicao(StatusOcorrencia.ENCERRADA.value)
        stmt = (
            select(func.avg(self._segundos_entre(despacho.c.em, encerramento.c.em)), func.count())
            .select_from(despacho)
            .join(encerramento, encerramento.c.ocorrencia_id == despacho.c.ocorrencia_id)
            .where(encerramento.c.em.between(_utc(de), _utc(ate)))
        )
        return await self._media(stmt)

    async def despachos_por_hora_utc(self, de: datetime, ate: datetime) -> dict[int, int]:
        hora = self._hora_utc(OrdemDespachoModel.criada_em).label("hora")
        stmt = (
            select(hora, func.count())
            .where(OrdemDespachoModel.criada_em.between(_utc(de), _utc(ate)))
            .group_by(hora)
        )
        return await self._contagem(stmt)

    async def viaturas_por_situacao(self) -> dict[str, int]:
        return await self._contagem(select(ViaturaModel.situacao, func.count()).group_by(ViaturaModel.situacao))
