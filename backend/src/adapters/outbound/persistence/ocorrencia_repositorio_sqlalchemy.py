"""
Adapter de saída: OcorrenciaRepositorioSQLAlchemy

Implementação concreta de RepositorioOcorrencia usando SQLAlchemy async.
Apenas este arquivo pode importar models SQLAlchemy — nunca domain/ nem application/.

- Não confirma transação (papel da UnidadeDeTrabalho).
- Nunca apaga filhos: envolvidos/tipificações removidos do agregado ficam ``ativo=False`` (RNF03*).
- Optimistic locking via ``versao`` (RNF11): a versão carregada é rastreada por
  instância (uma por request); ao salvar, a linha é travada (``FOR UPDATE`` no
  Postgres) e comparada — divergência → ConflitoError (409).
"""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from adapters.outbound.persistence._datas import aware
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from domain.ocorrencia.entity import (
    Envolvido,
    Ocorrencia,
    RegistroHistoricoStatus,
    TipificacaoPenal,
    TipoEnvolvido,
)
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import ConflitoError
from domain.shared.geo import Coordenada
from infrastructure.database.models import (
    EnvolvidoModel,
    HistoricoStatusModel,
    OcorrenciaModel,
    TipificacaoModel,
)

_CARREGAR_FILHOS = (
    selectinload(OcorrenciaModel.envolvidos),
    selectinload(OcorrenciaModel.tipificacoes),
    selectinload(OcorrenciaModel.historico),
)


class OcorrenciaRepositorioSQLAlchemy(RepositorioOcorrencia):
    """Repositório de ocorrências com persistência relacional via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
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
        existente = await self._carregar_model(ocorrencia.id)
        if existente is None:
            self._session.add(self._to_model(ocorrencia))
        else:
            await self._verificar_versao(ocorrencia)
            self._atualizar_model(existente, ocorrencia)
        await self._session.flush()
        self._versoes_carregadas[ocorrencia.id] = ocorrencia.versao

    async def buscar_por_id(self, ocorrencia_id: UUID) -> Ocorrencia | None:
        model = await self._carregar_model(ocorrencia_id)
        if model is None:
            return None
        self._versoes_carregadas[model.id] = model.versao
        return self._to_domain(model)

    def _aplicar_filtro(self, stmt, filtro: FiltroOcorrencias):
        if filtro.status:
            stmt = stmt.where(OcorrenciaModel.status.in_([s.value for s in filtro.status]))
        if filtro.agente_policial_id:
            stmt = stmt.where(OcorrenciaModel.agente_policial_id == filtro.agente_policial_id)
        return stmt

    async def listar(self, filtro: FiltroOcorrencias) -> list[Ocorrencia]:
        stmt = self._aplicar_filtro(select(OcorrenciaModel), filtro)
        stmt = stmt.options(*_CARREGAR_FILHOS).order_by(OcorrenciaModel.criada_em.asc()).limit(filtro.limit).offset(filtro.offset)
        models = (await self._session.execute(stmt)).scalars().all()
        for m in models:
            self._versoes_carregadas[m.id] = m.versao
        return [self._to_domain(m) for m in models]

    async def contar(self, filtro: FiltroOcorrencias) -> int:
        stmt = self._aplicar_filtro(select(func.count(OcorrenciaModel.id)), filtro)
        return int((await self._session.execute(stmt)).scalar_one())

    # ------------------------------------------------------------- mapeamento
    @staticmethod
    def _campos_escalares(ocorrencia: Ocorrencia) -> dict:
        return dict(
            agente_policial_id=ocorrencia.agente_policial_id,
            natureza=ocorrencia.natureza,
            descricao=ocorrencia.descricao,
            localizacao=ocorrencia.localizacao,
            latitude=ocorrencia.coordenada.latitude,
            longitude=ocorrencia.coordenada.longitude,
            data_hora_fato=ocorrencia.data_hora_fato,
            numero_protocolo=ocorrencia.numero_protocolo,
            status=ocorrencia.status.value,
            versao=ocorrencia.versao,
            criada_em=ocorrencia.criada_em,
            atualizada_em=ocorrencia.atualizada_em,
            validada_por_id=ocorrencia.validada_por_id,
            justificativa_revisao=ocorrencia.justificativa_revisao,
            desfecho=ocorrencia.desfecho,
            hash_narrativa=ocorrencia.hash_narrativa,
        )

    def _to_model(self, ocorrencia: Ocorrencia) -> OcorrenciaModel:
        model = OcorrenciaModel(id=ocorrencia.id, **self._campos_escalares(ocorrencia))
        model.envolvidos = [
            EnvolvidoModel(id=e.id, nome=e.nome, tipo=e.tipo.value, documento=e.documento, ativo=True)
            for e in ocorrencia.envolvidos
        ]
        model.tipificacoes = [
            TipificacaoModel(artigo=t.artigo, descricao=t.descricao, ativo=True) for t in ocorrencia.tipificacoes
        ]
        model.historico = [self._historico_model(ocorrencia.id, i, h) for i, h in enumerate(ocorrencia.historico_status)]
        return model

    def _atualizar_model(self, model: OcorrenciaModel, ocorrencia: Ocorrencia) -> None:
        for campo, valor in self._campos_escalares(ocorrencia).items():
            setattr(model, campo, valor)

        # envolvidos: desativa os removidos, insere os novos, atualiza os mantidos
        atuais = {e.id: e for e in ocorrencia.envolvidos}
        for em in model.envolvidos:
            if em.id in atuais:
                e = atuais.pop(em.id)
                em.nome, em.tipo, em.documento, em.ativo = e.nome, e.tipo.value, e.documento, True
            else:
                em.ativo = False
        for e in atuais.values():
            model.envolvidos.append(
                EnvolvidoModel(id=e.id, nome=e.nome, tipo=e.tipo.value, documento=e.documento, ativo=True)
            )

        # tipificações: chave natural (artigo, descricao)
        desejadas = {(t.artigo, t.descricao) for t in ocorrencia.tipificacoes}
        presentes: set[tuple[str, str]] = set()
        for tm in model.tipificacoes:
            chave = (tm.artigo, tm.descricao)
            tm.ativo = chave in desejadas
            if tm.ativo:
                presentes.add(chave)
        for artigo, descricao in desejadas - presentes:
            model.tipificacoes.append(TipificacaoModel(artigo=artigo, descricao=descricao, ativo=True))

        # histórico: append-only
        ja_gravados = len(model.historico)
        for i, h in enumerate(ocorrencia.historico_status[ja_gravados:], start=ja_gravados):
            model.historico.append(self._historico_model(ocorrencia.id, i, h))

    @staticmethod
    def _historico_model(ocorrencia_id: UUID, ordem: int, h: RegistroHistoricoStatus) -> HistoricoStatusModel:
        return HistoricoStatusModel(
            ocorrencia_id=ocorrencia_id,
            ordem=ordem,
            de=h.de.value if h.de else None,
            para=h.para.value,
            em=h.em,
            por_id=h.por_id,
            justificativa=h.justificativa,
        )

    def _to_domain(self, model: OcorrenciaModel) -> Ocorrencia:
        ocorrencia = Ocorrencia(
            id=model.id,
            agente_policial_id=model.agente_policial_id,
            natureza=model.natureza,
            descricao=model.descricao,
            localizacao=model.localizacao,
            coordenada=Coordenada(model.latitude, model.longitude),
            data_hora_fato=aware(model.data_hora_fato),
            numero_protocolo=model.numero_protocolo,
            status=StatusOcorrencia(model.status),
            versao=model.versao,
            criada_em=aware(model.criada_em),
            atualizada_em=aware(model.atualizada_em),
            validada_por_id=model.validada_por_id,
            justificativa_revisao=model.justificativa_revisao,
            desfecho=model.desfecho,
            hash_narrativa=model.hash_narrativa,
        )
        ocorrencia.envolvidos = [
            Envolvido(id=e.id, nome=e.nome, tipo=TipoEnvolvido(e.tipo), documento=e.documento)
            for e in model.envolvidos
            if e.ativo
        ]
        ocorrencia.tipificacoes = [
            TipificacaoPenal(artigo=t.artigo, descricao=t.descricao) for t in model.tipificacoes if t.ativo
        ]
        ocorrencia.historico_status = [
            RegistroHistoricoStatus(
                de=StatusOcorrencia(h.de) if h.de else None,
                para=StatusOcorrencia(h.para),
                em=aware(h.em),
                por_id=h.por_id,
                justificativa=h.justificativa,
            )
            for h in sorted(model.historico, key=lambda h: h.ordem)
        ]
        return ocorrencia
