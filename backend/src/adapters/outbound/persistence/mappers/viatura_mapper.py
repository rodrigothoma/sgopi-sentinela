"""
Data Mapper para a entidade Viatura (HEX-03 / SRP).

Isola a lógica de conversão bidirecional entre Viatura (Domain) e ViaturaModel (SQLAlchemy).
"""
from __future__ import annotations

from adapters.outbound.persistence._datas import aware
from domain.shared.geo import Coordenada
from domain.viatura.entity import Posicao, SituacaoViatura, Viatura
from infrastructure.database.models import ViaturaModel


class ViaturaMapper:
    """Mapeamento bidirecional entre a entidade Viatura e o modelo relacional ViaturaModel."""

    @staticmethod
    def atualizar_model(model: ViaturaModel, viatura: Viatura) -> None:
        """Sincroniza os atributos escalares e a última posição conhecida da viatura no modelo ORM.

        Args:
            model: Instância do modelo SQLAlchemy a ser atualizado.
            viatura: Entidade de domínio Viatura com os dados mais recentes.
        """
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
        """Cria e preenche uma nova instância de ViaturaModel a partir da entidade de domínio.

        Args:
            viatura: Entidade Viatura.

        Returns:
            ViaturaModel: Modelo ORM pronto para inclusão na sessão.
        """
        model = ViaturaModel(id=viatura.id)
        cls.atualizar_model(model, viatura)
        return model

    @staticmethod
    def to_domain(m: ViaturaModel) -> Viatura:
        """Reconstitui a entidade Viatura a partir de um registro ViaturaModel.

        Garante a reconstrução do Value Object Coordenada e Posicao com timezone consciente.

        Args:
            m: Registro ORM ViaturaModel do banco.

        Returns:
            Viatura: Entidade de domínio reconstituída.
        """
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
            atualizada_em=aware(m.atualizada_em) if m.atualizada_em else None,
        )
