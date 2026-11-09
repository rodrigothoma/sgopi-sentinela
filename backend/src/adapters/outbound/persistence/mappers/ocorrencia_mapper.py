"""
Data Mapper para o agregado Ocorrencia (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre Ocorrencia (Domain) e OcorrenciaModel (SQLAlchemy).
Garante a reconciliação de coleções filhas sob a regra RNF03 (soft-delete e append-only).
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from adapters.outbound.persistence._datas import aware
from domain.ocorrencia.apreensao import (
    EstadoConservacao,
    ItemApreendido,
    MovimentacaoCustodia,
    TipoItemApreendido,
    UnidadeMedida,
)
from domain.ocorrencia.entity import (
    Envolvido,
    Evidencia,
    Ocorrencia,
    OrigemOcorrencia,
    RegistroHistoricoStatus,
    TipificacaoPenal,
    TipoEnvolvido,
)
from domain.ocorrencia.prioridade import PrioridadeOcorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.geo import Coordenada
from infrastructure.database.models import (
    EnvolvidoModel,
    EvidenciaModel,
    HistoricoStatusModel,
    ItemApreendidoModel,
    MovimentacaoCustodiaModel,
    OcorrenciaModel,
    TipificacaoModel,
)


class OcorrenciaMapper:
    """Mapeamento bidirecional e reconciliação entre Ocorrencia e OcorrenciaModel."""

    # -------------------------------------------------------------------------
    # API Pública do Mapper
    # -------------------------------------------------------------------------
    @classmethod
    def to_model(cls, ocorrencia: Ocorrencia) -> OcorrenciaModel:
        """Instancia um novo OcorrenciaModel inicializado com todos os filhos a partir do domínio."""
        model = OcorrenciaModel(id=ocorrencia.id, **cls._campos_escalares(ocorrencia))
        model.envolvidos = [cls._envolvido_model(e) for e in ocorrencia.envolvidos]
        model.tipificacoes = [TipificacaoModel(artigo=t.artigo, descricao=t.descricao, ativo=True) for t in ocorrencia.tipificacoes]
        model.evidencias = [cls._evidencia_model(e) for e in ocorrencia.evidencias]
        model.itens_apreendidos = [cls._item_model(i) for i in ocorrencia.itens_apreendidos]
        model.historico = [cls._historico_model(ocorrencia.id, i, h) for i, h in enumerate(ocorrencia.historico_status)]
        return model

    @classmethod
    def to_domain(cls, model: OcorrenciaModel) -> Ocorrencia:
        """Reconstitui a entidade rica Ocorrencia a partir do OcorrenciaModel e seus relacionamentos."""
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
            hash_versao=model.hash_versao,
            chave_autenticidade=model.chave_autenticidade,
            arquivada_por_id=model.arquivada_por_id,
            motivo_arquivamento=model.motivo_arquivamento,
            excluida_por_id=model.excluida_por_id,
            motivo_exclusao=model.motivo_exclusao,
            inquerito_id=model.inquerito_id,
            origem=OrigemOcorrencia(model.origem),
            codigo_acompanhamento_hash=model.codigo_acompanhamento_hash,
            prioridade=PrioridadeOcorrencia(model.prioridade),
        )
        ocorrencia.envolvidos = cls._envolvidos_dominio(model.envolvidos)
        ocorrencia.tipificacoes = cls._tipificacoes_dominio(model.tipificacoes)
        ocorrencia.evidencias = cls._evidencias_dominio(model.evidencias)
        ocorrencia.itens_apreendidos = cls._itens_dominio(model.itens_apreendidos)
        ocorrencia.historico_status = cls._historico_dominio(model.historico)
        return ocorrencia

    @classmethod
    def atualizar_model(cls, model: OcorrenciaModel, ocorrencia: Ocorrencia) -> None:
        """Reconcilia um OcorrenciaModel existente com as alterações da entidade de domínio (RNF03)."""
        for campo, valor in cls._campos_escalares(ocorrencia).items():
            setattr(model, campo, valor)

        cls._sincronizar_envolvidos(model, ocorrencia.envolvidos)
        cls._sincronizar_tipificacoes(model, ocorrencia.tipificacoes)
        cls._sincronizar_evidencias(model, ocorrencia.evidencias)
        cls._sincronizar_itens_apreendidos(model, ocorrencia.itens_apreendidos)
        cls._sincronizar_historico(model, ocorrencia.id, ocorrencia.historico_status)

    # -------------------------------------------------------------------------
    # Auxiliares Privados de Conversão: Domínio -> Model
    # -------------------------------------------------------------------------
    @staticmethod
    def _campos_escalares(ocorrencia: Ocorrencia) -> dict[str, Any]:
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
            hash_versao=ocorrencia.hash_versao,
            chave_autenticidade=ocorrencia.chave_autenticidade,
            arquivada_por_id=ocorrencia.arquivada_por_id,
            motivo_arquivamento=ocorrencia.motivo_arquivamento,
            excluida_por_id=ocorrencia.excluida_por_id,
            motivo_exclusao=ocorrencia.motivo_exclusao,
            inquerito_id=ocorrencia.inquerito_id,
            origem=ocorrencia.origem.value,
            prioridade=ocorrencia.prioridade.value,
            codigo_acompanhamento_hash=ocorrencia.codigo_acompanhamento_hash,
        )

    @staticmethod
    def _envolvido_model(e: Envolvido) -> EnvolvidoModel:
        return EnvolvidoModel(
            id=e.id,
            nome=e.nome,
            tipo=e.tipo.value,
            documento=e.documento,
            email=e.email,
            telefone=e.telefone,
            ativo=True,
        )

    @staticmethod
    def _evidencia_model(e: Evidencia) -> EvidenciaModel:
        return EvidenciaModel(
            id=e.id,
            nome_original=e.nome_original,
            formato=e.formato,
            tamanho=e.tamanho,
            hash_sha256=e.hash_sha256,
            chave_armazenamento=e.chave_armazenamento,
            enviada_em=e.enviada_em,
        )

    @classmethod
    def _item_model(cls, item: ItemApreendido) -> ItemApreendidoModel:
        model = ItemApreendidoModel(
            id=item.id,
            tipo=item.tipo.value,
            descricao=item.descricao,
            quantidade=item.quantidade,
            unidade=item.unidade.value,
            estado_conservacao=item.estado_conservacao.value,
            numero_lacre=item.numero_lacre,
            numero_serie=item.numero_serie,
            marca=item.marca,
            calibre=item.calibre,
            localizacao_deposito=item.localizacao_deposito,
            registrado_em=item.registrado_em,
            registrado_por_id=item.registrado_por_id,
        )
        model.movimentacoes = [cls._movimentacao_model(item.id, i, m) for i, m in enumerate(item.movimentacoes)]
        return model

    @staticmethod
    def _movimentacao_model(item_id: UUID, ordem: int, m: MovimentacaoCustodia) -> MovimentacaoCustodiaModel:
        return MovimentacaoCustodiaModel(
            item_id=item_id, ordem=ordem, em=m.em, por_id=m.por_id, origem=m.origem, destino=m.destino, observacao=m.observacao
        )

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

    # -------------------------------------------------------------------------
    # Auxiliares Privados de Reconciliação (RNF03)
    # -------------------------------------------------------------------------
    @classmethod
    def _sincronizar_envolvidos(cls, model: OcorrenciaModel, envolvidos: list[Envolvido]) -> None:
        atuais = {e.id: e for e in envolvidos}
        for em in model.envolvidos:
            if em.id in atuais:
                e = atuais.pop(em.id)
                em.nome, em.tipo, em.documento, em.email, em.telefone, em.ativo = (
                    e.nome,
                    e.tipo.value,
                    e.documento,
                    e.email,
                    e.telefone,
                    True,
                )
            else:
                em.ativo = False
        for e in atuais.values():
            model.envolvidos.append(cls._envolvido_model(e))

    @staticmethod
    def _sincronizar_tipificacoes(model: OcorrenciaModel, tipificacoes: list[TipificacaoPenal]) -> None:
        desejadas = {(t.artigo, t.descricao) for t in tipificacoes}
        presentes: set[tuple[str, str]] = set()
        for tm in model.tipificacoes:
            chave = (tm.artigo, tm.descricao)
            tm.ativo = chave in desejadas
            if tm.ativo:
                presentes.add(chave)
        for artigo, descricao in desejadas - presentes:
            model.tipificacoes.append(TipificacaoModel(artigo=artigo, descricao=descricao, ativo=True))

    @classmethod
    def _sincronizar_evidencias(cls, model: OcorrenciaModel, evidencias: list[Evidencia]) -> None:
        ids_gravados = {e.id for e in model.evidencias}
        for e in evidencias:
            if e.id not in ids_gravados:
                model.evidencias.append(cls._evidencia_model(e))

    @classmethod
    def _sincronizar_itens_apreendidos(cls, model: OcorrenciaModel, itens: list[ItemApreendido]) -> None:
        itens_gravados = {im.id: im for im in model.itens_apreendidos}
        for item in itens:
            gravado = itens_gravados.get(item.id)
            if gravado is None:
                model.itens_apreendidos.append(cls._item_model(item))
                continue
            ja = len(gravado.movimentacoes)
            for ordem, m in enumerate(item.movimentacoes[ja:], start=ja):
                gravado.movimentacoes.append(cls._movimentacao_model(item.id, ordem, m))

    @classmethod
    def _sincronizar_historico(
        cls, model: OcorrenciaModel, ocorrencia_id: UUID, historico: list[RegistroHistoricoStatus]
    ) -> None:
        ja_gravados = len(model.historico)
        for i, h in enumerate(historico[ja_gravados:], start=ja_gravados):
            model.historico.append(cls._historico_model(ocorrencia_id, i, h))

    # -------------------------------------------------------------------------
    # Auxiliares Privados de Conversão: Model -> Domínio
    # -------------------------------------------------------------------------
    @staticmethod
    def _envolvidos_dominio(models: list[EnvolvidoModel]) -> list[Envolvido]:
        return [
            Envolvido(
                id=e.id,
                nome=e.nome,
                tipo=TipoEnvolvido(e.tipo),
                documento=e.documento,
                email=e.email,
                telefone=e.telefone,
            )
            for e in models
            if e.ativo
        ]

    @staticmethod
    def _tipificacoes_dominio(models: list[TipificacaoModel]) -> list[TipificacaoPenal]:
        return [TipificacaoPenal(artigo=t.artigo, descricao=t.descricao) for t in models if t.ativo]

    @staticmethod
    def _evidencias_dominio(models: list[EvidenciaModel]) -> list[Evidencia]:
        return [
            Evidencia(
                id=e.id,
                nome_original=e.nome_original,
                formato=e.formato,
                tamanho=e.tamanho,
                hash_sha256=e.hash_sha256,
                chave_armazenamento=e.chave_armazenamento,
                enviada_em=aware(e.enviada_em),
            )
            for e in models
        ]

    @classmethod
    def _itens_dominio(cls, models: list[ItemApreendidoModel]) -> list[ItemApreendido]:
        return [
            ItemApreendido(
                id=i.id,
                tipo=TipoItemApreendido(i.tipo),
                descricao=i.descricao,
                quantidade=i.quantidade,
                unidade=UnidadeMedida(i.unidade),
                estado_conservacao=EstadoConservacao(i.estado_conservacao),
                numero_lacre=i.numero_lacre,
                numero_serie=i.numero_serie,
                marca=i.marca,
                calibre=i.calibre,
                localizacao_deposito=i.localizacao_deposito,
                registrado_em=aware(i.registrado_em),
                registrado_por_id=i.registrado_por_id,
                movimentacoes=[
                    MovimentacaoCustodia(
                        em=aware(m.em), por_id=m.por_id, origem=m.origem, destino=m.destino, observacao=m.observacao
                    )
                    for m in sorted(i.movimentacoes, key=lambda m: m.ordem)
                ],
            )
            for i in models
        ]

    @staticmethod
    def _historico_dominio(models: list[HistoricoStatusModel]) -> list[RegistroHistoricoStatus]:
        return [
            RegistroHistoricoStatus(
                de=StatusOcorrencia(h.de) if h.de else None,
                para=StatusOcorrencia(h.para),
                em=aware(h.em),
                por_id=h.por_id,
                justificativa=h.justificativa,
            )
            for h in sorted(models, key=lambda h: h.ordem)
        ]
