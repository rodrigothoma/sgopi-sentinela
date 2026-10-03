"""
Adapter de saída: Repositório e Gerador de Número de Ofício para Comunicação Interagências (RF10 / UC10).
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_comunicacao_interagencias import (
    GeradorNumeroOficio,
    RepositorioComunicacaoInteragencias,
)
from domain.interagencias.entity import (
    ComunicacaoInteragencias,
    NivelSigilo,
    PrioridadeComunicacao,
    StatusEntrega,
)
from infrastructure.database.models import ComunicacaoInteragenciasModel, SequenciaOficioModel


class GeradorNumeroOficioSQLAlchemy(GeradorNumeroOficio):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def proximo_numero(self, ano: int) -> str:
        stmt = (
            select(SequenciaOficioModel)
            .where(SequenciaOficioModel.ano == ano)
            .with_for_update()
        )
        seq = (await self._session.execute(stmt)).scalar_one_or_none()
        if seq is None:
            seq = SequenciaOficioModel(ano=ano, ultimo=0)
            self._session.add(seq)

        seq.ultimo += 1
        await self._session.flush()
        return f"OFI-{ano}-{seq.ultimo:06d}"


class ComunicacaoInteragenciasRepositorioSQLAlchemy(RepositorioComunicacaoInteragencias):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def salvar(self, comunicacao: ComunicacaoInteragencias) -> ComunicacaoInteragencias:
        stmt = select(ComunicacaoInteragenciasModel).where(ComunicacaoInteragenciasModel.id == comunicacao.id)
        existente = (await self._session.execute(stmt)).scalar_one_or_none()

        sigilo_str = comunicacao.nivel_sigilo.value if hasattr(comunicacao.nivel_sigilo, "value") else str(comunicacao.nivel_sigilo)
        prio_str = comunicacao.prioridade.value if hasattr(comunicacao.prioridade, "value") else str(comunicacao.prioridade)
        status_str = comunicacao.status_entrega.value if hasattr(comunicacao.status_entrega, "value") else str(comunicacao.status_entrega)

        if existente is None:
            model = ComunicacaoInteragenciasModel(
                id=comunicacao.id,
                numero_oficio=comunicacao.numero_oficio,
                protocolo_ocorrencia=comunicacao.protocolo_ocorrencia,
                departamento_origem=comunicacao.departamento_origem,
                departamentos_destinatarios=comunicacao.departamentos_destinatarios,
                remetente_id=comunicacao.remetente_id,
                assunto=comunicacao.assunto,
                corpo=comunicacao.corpo,
                nivel_sigilo=sigilo_str,
                prioridade=prio_str,
                status_entrega=status_str,
                mensagem_pai_id=comunicacao.mensagem_pai_id,
                criada_em=comunicacao.criada_em,
                ativo=comunicacao.ativo,
            )
            self._session.add(model)
        else:
            existente.status_entrega = status_str
            existente.ativo = comunicacao.ativo

        await self._session.flush()
        return comunicacao

    async def obter_por_id(self, comunicacao_id: UUID) -> ComunicacaoInteragencias | None:
        stmt = select(ComunicacaoInteragenciasModel).where(
            ComunicacaoInteragenciasModel.id == comunicacao_id,
            ComunicacaoInteragenciasModel.ativo.is_(True),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def listar(
        self,
        departamento: str | None = None,
        protocolo: str | None = None,
        remetente_id: UUID | None = None,
        limite: int = 50,
    ) -> list[ComunicacaoInteragencias]:
        stmt = select(ComunicacaoInteragenciasModel).where(ComunicacaoInteragenciasModel.ativo.is_(True))

        if protocolo:
            stmt = stmt.where(ComunicacaoInteragenciasModel.protocolo_ocorrencia == protocolo)
        if remetente_id:
            stmt = stmt.where(ComunicacaoInteragenciasModel.remetente_id == remetente_id)

        stmt = stmt.order_by(ComunicacaoInteragenciasModel.criada_em.desc()).limit(limite)
        models = (await self._session.execute(stmt)).scalars().all()

        # Filtragem em Python para suportar match em JSON (compatível com SQLite e Postgres)
        resultado = []
        for m in models:
            if departamento:
                dep_upper = departamento.upper()
                pertence = (
                    m.departamento_origem.upper() == dep_upper
                    or dep_upper in [d.upper() for d in (m.departamentos_destinatarios or [])]
                )
                if not pertence:
                    continue
            resultado.append(self._to_domain(m))

        return resultado

    async def listar_respostas(self, mensagem_pai_id: UUID) -> list[ComunicacaoInteragencias]:
        stmt = (
            select(ComunicacaoInteragenciasModel)
            .where(
                ComunicacaoInteragenciasModel.mensagem_pai_id == mensagem_pai_id,
                ComunicacaoInteragenciasModel.ativo.is_(True),
            )
            .order_by(ComunicacaoInteragenciasModel.criada_em.asc())
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: ComunicacaoInteragenciasModel) -> ComunicacaoInteragencias:
        return ComunicacaoInteragencias(
            id=model.id,
            numero_oficio=model.numero_oficio,
            protocolo_ocorrencia=model.protocolo_ocorrencia,
            departamento_origem=model.departamento_origem,
            departamentos_destinatarios=list(model.departamentos_destinatarios),
            remetente_id=model.remetente_id,
            assunto=model.assunto,
            corpo=model.corpo,
            nivel_sigilo=NivelSigilo(model.nivel_sigilo) if model.nivel_sigilo in NivelSigilo.__members__ else NivelSigilo.PADRAO,
            prioridade=PrioridadeComunicacao(model.prioridade) if model.prioridade in PrioridadeComunicacao.__members__ else PrioridadeComunicacao.MEDIA,
            status_entrega=StatusEntrega(model.status_entrega) if model.status_entrega in StatusEntrega.__members__ else StatusEntrega.ENTREGUE,
            mensagem_pai_id=model.mensagem_pai_id,
            criada_em=aware(model.criada_em),
            ativo=model.ativo,
        )
