"""
Data Mapper para a entidade LaudoPericial (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre LaudoPericial (Domain) e LaudoPericialModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware, aware_opcional
from domain.laudo.entity import LaudoPericial, StatusLaudo, TipoPericia
from infrastructure.database.models import LaudoPericialModel


class LaudoMapper:
    """Mapeamento bidirecional entre a entidade LaudoPericial e o modelo relacional LaudoPericialModel."""

    @staticmethod
    def atualizar_model(model: LaudoPericialModel, laudo: LaudoPericial) -> None:
        """Copia só os campos mutáveis; a solicitação (tipo, descrição, vínculos) não muda depois de registrada."""
        model.perito_id = laudo.perito_id
        model.conclusoes_tecnicas = laudo.conclusoes_tecnicas
        model.arquivo_chave = laudo.arquivo_chave
        model.arquivo_nome = laudo.arquivo_nome
        model.hash_sha256 = laudo.hash_sha256
        model.status = laudo.status.value
        model.concluido_em = laudo.concluido_em
        model.atualizado_em = laudo.atualizado_em
        model.ativo = laudo.ativo
        model.versao = laudo.versao

    @staticmethod
    def to_model(laudo: LaudoPericial) -> LaudoPericialModel:
        return LaudoPericialModel(
            id=laudo.id,
            numero_referencia=laudo.numero_referencia,
            tipo_pericia=laudo.tipo_pericia.value,
            descricao_solicitacao=laudo.descricao_solicitacao,
            solicitante_id=laudo.solicitante_id,
            perito_id=laudo.perito_id,
            ocorrencia_id=laudo.ocorrencia_id,
            inquerito_id=laudo.inquerito_id,
            item_apreendido_id=laudo.item_apreendido_id,
            conclusoes_tecnicas=laudo.conclusoes_tecnicas,
            arquivo_chave=laudo.arquivo_chave,
            arquivo_nome=laudo.arquivo_nome,
            hash_sha256=laudo.hash_sha256,
            status=laudo.status.value,
            solicitado_em=laudo.solicitado_em,
            concluido_em=laudo.concluido_em,
            atualizado_em=laudo.atualizado_em,
            ativo=laudo.ativo,
            versao=laudo.versao,
        )

    @staticmethod
    def to_domain(model: LaudoPericialModel) -> LaudoPericial:
        return LaudoPericial(
            id=model.id,
            numero_referencia=model.numero_referencia,
            tipo_pericia=TipoPericia(model.tipo_pericia),
            descricao_solicitacao=model.descricao_solicitacao,
            solicitante_id=model.solicitante_id,
            perito_id=model.perito_id,
            ocorrencia_id=model.ocorrencia_id,
            inquerito_id=model.inquerito_id,
            item_apreendido_id=model.item_apreendido_id,
            conclusoes_tecnicas=model.conclusoes_tecnicas,
            arquivo_chave=model.arquivo_chave,
            arquivo_nome=model.arquivo_nome,
            hash_sha256=model.hash_sha256,
            status=StatusLaudo(model.status),
            solicitado_em=aware(model.solicitado_em),
            concluido_em=aware_opcional(model.concluido_em),
            atualizado_em=aware_opcional(model.atualizado_em),
            ativo=model.ativo,
            versao=model.versao,
        )
