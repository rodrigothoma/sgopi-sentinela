"""
Data Mapper para a entidade Inquerito (HEX-03 / SRP).

Isola a lógica de conversão entre Inquerito (Domain) e InqueritoModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware, aware_opcional
from domain.inquerito.entity import Inquerito, StatusInquerito
from domain.ocorrencia.status import StatusOcorrencia
from infrastructure.database.models import InqueritoModel


class InqueritoMapper:
    """Mapeamento entre a entidade Inquerito e o modelo relacional InqueritoModel.

    ``ocorrencias_ids`` só é mapeado na leitura: o vínculo é a coluna ``ocorrencias.inquerito_id``,
    gravada pelo OcorrenciaMapper quando o caso de uso salva cada ocorrência vinculada.
    """

    @staticmethod
    def atualizar_model(model: InqueritoModel, inquerito: Inquerito) -> None:
        """Copia só os campos mutáveis; número, delegado e data de abertura não mudam após a instauração."""
        model.ementa = inquerito.ementa
        model.status = inquerito.status.value
        model.relatorio_final = inquerito.relatorio_final
        model.motivo_arquivamento = inquerito.motivo_arquivamento
        model.concluido_em = inquerito.concluido_em
        model.atualizado_em = inquerito.atualizado_em
        model.ativo = inquerito.ativo
        model.versao = inquerito.versao

    @staticmethod
    def to_model(inquerito: Inquerito) -> InqueritoModel:
        return InqueritoModel(
            id=inquerito.id,
            numero=inquerito.numero,
            ementa=inquerito.ementa,
            delegado_id=inquerito.delegado_id,
            status=inquerito.status.value,
            relatorio_final=inquerito.relatorio_final,
            motivo_arquivamento=inquerito.motivo_arquivamento,
            data_abertura=inquerito.data_abertura,
            concluido_em=inquerito.concluido_em,
            atualizado_em=inquerito.atualizado_em,
            ativo=inquerito.ativo,
            versao=inquerito.versao,
        )

    @staticmethod
    def to_domain(model: InqueritoModel) -> Inquerito:
        """Exige ``model.ocorrencias`` já carregado; ocorrências excluídas logicamente ficam de fora."""
        return Inquerito(
            id=model.id,
            numero=model.numero,
            ementa=model.ementa,
            delegado_id=model.delegado_id,
            status=StatusInquerito(model.status),
            data_abertura=aware(model.data_abertura),
            atualizado_em=aware_opcional(model.atualizado_em),
            concluido_em=aware_opcional(model.concluido_em),
            relatorio_final=model.relatorio_final,
            motivo_arquivamento=model.motivo_arquivamento,
            ativo=model.ativo,
            versao=model.versao,
            ocorrencias_ids=[oc.id for oc in model.ocorrencias if oc.status != StatusOcorrencia.EXCLUIDA.value],
        )
