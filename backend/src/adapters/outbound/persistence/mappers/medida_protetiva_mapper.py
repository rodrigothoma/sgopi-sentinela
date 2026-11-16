"""
Data Mapper para a entidade MedidaProtetiva (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre MedidaProtetiva (Domain) e MedidaProtetivaModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware, aware_opcional
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from infrastructure.database.models import MedidaProtetivaModel


class MedidaProtetivaMapper:
    """Mapeamento bidirecional entre a entidade MedidaProtetiva e o modelo relacional MedidaProtetivaModel.

    ``tipos_restricao`` é sempre copiada: coluna JSON não rastreia mutação in-place, então uma lista
    compartilhada entre entidade e model faria o ORM não enxergar a alteração e omitir o UPDATE.
    """

    @staticmethod
    def atualizar_model(model: MedidaProtetivaModel, medida: MedidaProtetiva) -> None:
        """Copia só os campos mutáveis; partes, ocorrência e data de início não mudam após a concessão."""
        model.tipos_restricao = list(medida.tipos_restricao)
        model.distancia_minima_metros = medida.distancia_minima_metros
        model.prazo_dias = medida.prazo_dias
        model.data_vencimento = medida.data_vencimento
        model.condicoes_especificas = medida.condicoes_especificas
        model.motivo_revogacao = medida.motivo_revogacao
        model.justificativa_renovacao = medida.justificativa_renovacao
        model.status = medida.status.value
        model.atualizada_em = medida.atualizada_em
        model.ativo = medida.ativo
        model.versao = medida.versao
        model.alerta_vencimento_enviado_em = medida.alerta_vencimento_enviado_em

    @staticmethod
    def to_model(medida: MedidaProtetiva) -> MedidaProtetivaModel:
        return MedidaProtetivaModel(
            id=medida.id,
            numero_referencia=medida.numero_referencia,
            ocorrencia_id=medida.ocorrencia_id,
            delegado_id=medida.delegado_id,
            vitima_id=medida.vitima_id,
            agressor_id=medida.agressor_id,
            tipos_restricao=list(medida.tipos_restricao),
            distancia_minima_metros=medida.distancia_minima_metros,
            data_inicio=medida.data_inicio,
            prazo_dias=medida.prazo_dias,
            data_vencimento=medida.data_vencimento,
            condicoes_especificas=medida.condicoes_especificas,
            motivo_revogacao=medida.motivo_revogacao,
            justificativa_renovacao=medida.justificativa_renovacao,
            status=medida.status.value,
            criada_em=medida.criada_em,
            atualizada_em=medida.atualizada_em,
            ativo=medida.ativo,
            versao=medida.versao,
            alerta_vencimento_enviado_em=medida.alerta_vencimento_enviado_em,
        )

    @staticmethod
    def to_domain(model: MedidaProtetivaModel) -> MedidaProtetiva:
        return MedidaProtetiva(
            id=model.id,
            numero_referencia=model.numero_referencia,
            ocorrencia_id=model.ocorrencia_id,
            delegado_id=model.delegado_id,
            vitima_id=model.vitima_id,
            agressor_id=model.agressor_id,
            tipos_restricao=list(model.tipos_restricao),
            distancia_minima_metros=model.distancia_minima_metros,
            data_inicio=model.data_inicio,
            prazo_dias=model.prazo_dias,
            data_vencimento=model.data_vencimento,
            condicoes_especificas=model.condicoes_especificas,
            motivo_revogacao=model.motivo_revogacao,
            justificativa_renovacao=model.justificativa_renovacao,
            status=StatusMedida(model.status),
            criada_em=aware(model.criada_em),
            atualizada_em=aware_opcional(model.atualizada_em),
            ativo=model.ativo,
            versao=model.versao,
            alerta_vencimento_enviado_em=aware_opcional(model.alerta_vencimento_enviado_em),
        )
