"""
Data Mapper para a entidade Viatura (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre Viatura (Domain) e ViaturaModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware, aware_opcional
from domain.shared.geo import Coordenada
from domain.viatura.entity import Posicao, SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel


class ViaturaMapper:
    """Mapeamento bidirecional entre a entidade Viatura e o modelo relacional ViaturaModel."""

    @staticmethod
    def atualizar_model(model: ViaturaModel, viatura: Viatura) -> None:
        """A última posição conhecida é achatada nas colunas de latitude, longitude e instante do registro."""
        p = viatura.ultima_posicao
        model.prefixo = viatura.prefixo
        model.placa = viatura.placa
        model.situacao = viatura.situacao.value
        model.versao = viatura.versao
        model.atualizada_em = viatura.atualizada_em
        model.latitude = p.coordenada.latitude if p else None
        model.longitude = p.coordenada.longitude if p else None
        model.posicao_registrada_em = p.registrada_em if p else None

    @classmethod
    def to_model(cls, viatura: Viatura) -> ViaturaModel:
        model = ViaturaModel(id=viatura.id)
        cls.atualizar_model(model, viatura)
        return model

    @staticmethod
    def to_domain(m: ViaturaModel) -> Viatura:
        """A posição só é reconstituída quando latitude, longitude e instante estão todos preenchidos."""
        posicao = None
        if m.latitude is not None and m.longitude is not None and m.posicao_registrada_em is not None:
            posicao = Posicao(coordenada=Coordenada(m.latitude, m.longitude), registrada_em=aware(m.posicao_registrada_em))
        return Viatura(
            id=m.id,
            prefixo=m.prefixo,
            placa=m.placa,
            situacao=SituacaoViatura(m.situacao),
            ultima_posicao=posicao,
            versao=m.versao,
            atualizada_em=aware_opcional(m.atualizada_em),
        )
