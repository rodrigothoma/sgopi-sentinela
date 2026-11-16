"""
Data Mapper para a entidade ComunicacaoInteragencias (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre ComunicacaoInteragencias (Domain) e
ComunicacaoInteragenciasModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware
from domain.interagencias.entity import (
    ComunicacaoInteragencias,
    NivelSigilo,
    PrioridadeComunicacao,
    StatusEntrega,
)
from domain.shared.enums import interpretar_enum_ou_padrao
from infrastructure.database.models import ComunicacaoInteragenciasModel


class ComunicacaoInteragenciasMapper:
    """Mapeamento bidirecional entre a entidade ComunicacaoInteragencias e ComunicacaoInteragenciasModel."""

    @staticmethod
    def atualizar_model(model: ComunicacaoInteragenciasModel, comunicacao: ComunicacaoInteragencias) -> None:
        """Só a tramitação e a retirada lógica são regravadas; o ofício enviado é um documento rastreável."""
        model.status_entrega = comunicacao.status_entrega.value
        model.ativo = comunicacao.ativo

    @staticmethod
    def to_model(comunicacao: ComunicacaoInteragencias) -> ComunicacaoInteragenciasModel:
        return ComunicacaoInteragenciasModel(
            id=comunicacao.id,
            numero_oficio=comunicacao.numero_oficio,
            protocolo_ocorrencia=comunicacao.protocolo_ocorrencia,
            departamento_origem=comunicacao.departamento_origem,
            departamentos_destinatarios=list(comunicacao.departamentos_destinatarios),
            remetente_id=comunicacao.remetente_id,
            assunto=comunicacao.assunto,
            corpo=comunicacao.corpo,
            nivel_sigilo=comunicacao.nivel_sigilo.value,
            prioridade=comunicacao.prioridade.value,
            status_entrega=comunicacao.status_entrega.value,
            mensagem_pai_id=comunicacao.mensagem_pai_id,
            criada_em=comunicacao.criada_em,
            ativo=comunicacao.ativo,
        )

    @staticmethod
    def to_domain(model: ComunicacaoInteragenciasModel) -> ComunicacaoInteragencias:
        """Valor de enum que não existe mais cai no padrão, para um ofício antigo não quebrar a listagem."""
        return ComunicacaoInteragencias(
            id=model.id,
            numero_oficio=model.numero_oficio,
            protocolo_ocorrencia=model.protocolo_ocorrencia,
            departamento_origem=model.departamento_origem,
            departamentos_destinatarios=list(model.departamentos_destinatarios),
            remetente_id=model.remetente_id,
            assunto=model.assunto,
            corpo=model.corpo,
            nivel_sigilo=interpretar_enum_ou_padrao(NivelSigilo, model.nivel_sigilo, NivelSigilo.PADRAO),
            prioridade=interpretar_enum_ou_padrao(PrioridadeComunicacao, model.prioridade, PrioridadeComunicacao.MEDIA),
            status_entrega=interpretar_enum_ou_padrao(StatusEntrega, model.status_entrega, StatusEntrega.ENTREGUE),
            mensagem_pai_id=model.mensagem_pai_id,
            criada_em=aware(model.criada_em),
            ativo=model.ativo,
        )
