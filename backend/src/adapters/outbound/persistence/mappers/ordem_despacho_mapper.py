"""
Data Mapper para a entidade OrdemDeDespacho (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre OrdemDeDespacho (Domain) e OrdemDespachoModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware, aware_opcional
from domain.despacho.entity import OrdemDeDespacho
from infrastructure.database.models import OrdemDespachoModel


class OrdemDespachoMapper:
    """Mapeamento bidirecional entre a entidade OrdemDeDespacho e o modelo relacional OrdemDespachoModel."""

    @staticmethod
    def atualizar_model(model: OrdemDespachoModel, ordem: OrdemDeDespacho) -> None:
        model.numero = ordem.numero
        model.ocorrencia_id = ordem.ocorrencia_id
        model.viatura_id = ordem.viatura_id
        model.operador_id = ordem.operador_id
        model.criada_em = ordem.criada_em
        model.observacoes = ordem.observacoes
        model.ativa = ordem.ativa
        model.encerrada_em = ordem.encerrada_em
        model.apoio = ordem.apoio

    @classmethod
    def to_model(cls, ordem: OrdemDeDespacho) -> OrdemDespachoModel:
        model = OrdemDespachoModel(id=ordem.id)
        cls.atualizar_model(model, ordem)
        return model

    @staticmethod
    def to_domain(model: OrdemDespachoModel) -> OrdemDeDespacho:
        return OrdemDeDespacho(
            id=model.id,
            numero=model.numero,
            ocorrencia_id=model.ocorrencia_id,
            viatura_id=model.viatura_id,
            operador_id=model.operador_id,
            criada_em=aware(model.criada_em),
            observacoes=model.observacoes,
            ativa=model.ativa,
            encerrada_em=aware_opcional(model.encerrada_em),
            apoio=model.apoio,
        )
