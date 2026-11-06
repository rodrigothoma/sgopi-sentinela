"""Testes unitários puros do OcorrenciaMapper (sem dependência de banco de dados)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from adapters.outbound.persistence.mappers.ocorrencia_mapper import OcorrenciaMapper
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

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def _criar_ocorrencia_completa() -> Ocorrencia:
    """Instancia uma ocorrência de domínio completa para testes de mapeamento."""
    o_id = uuid4()
    agente_id = uuid4()
    item_id = uuid4()
    return Ocorrencia(
        id=o_id,
        agente_policial_id=agente_id,
        natureza="Roubo a Estabelecimento",
        descricao="Subtração mediante grave ameaça com arma de fogo.",
        localizacao="Rua das Flores, 123",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=2),
        numero_protocolo="SGOPI-2026-999999",
        status=StatusOcorrencia.EM_ATENDIMENTO,
        versao=2,
        criada_em=AGORA - timedelta(hours=1),
        atualizada_em=AGORA,
        origem=OrigemOcorrencia.POLICIAL,
        prioridade=PrioridadeOcorrencia.ALTA,
        codigo_acompanhamento_hash="hash_teste",
        envolvidos=[
            Envolvido(id=uuid4(), nome="Vítima Teste", tipo=TipoEnvolvido.VITIMA, documento="12345678900"),
            Envolvido(id=uuid4(), nome="Suspeito Teste", tipo=TipoEnvolvido.SUSPEITO),
        ],
        tipificacoes=[TipificacaoPenal(artigo="Art. 157 CP", descricao="Roubo qualificado")],
        evidencias=[
            Evidencia(
                id=uuid4(),
                nome_original="camera.mp4",
                formato="video/mp4",
                tamanho=10240,
                hash_sha256="a" * 64,
                chave_armazenamento="evidencias/camera.mp4",
                enviada_em=AGORA,
            )
        ],
        itens_apreendidos=[
            ItemApreendido(
                id=item_id,
                tipo=TipoItemApreendido.ARMA_DE_FOGO,
                descricao="Revólver Calibre .38",
                quantidade=1,
                estado_conservacao=EstadoConservacao.REGULAR,
                numero_lacre="LACRE-12345",
                localizacao_deposito="Cofre 01, Gaveta B",
                registrado_em=AGORA,
                registrado_por_id=agente_id,
                unidade=UnidadeMedida.UNIDADE,
                numero_serie="ABC999",
                marca="Taurus",
                calibre=".38",
                movimentacoes=[
                    MovimentacaoCustodia(
                        em=AGORA,
                        por_id=agente_id,
                        origem="Local do fato",
                        destino="Depósito Central",
                        observacao="Recolhido para perícia.",
                    )
                ],
            )
        ],
        historico_status=[
            RegistroHistoricoStatus(
                de=None,
                para=StatusOcorrencia.AGUARDANDO_REVISAO,
                em=AGORA - timedelta(hours=1),
                por_id=agente_id,
                justificativa="Registro inicial",
            ),
            RegistroHistoricoStatus(
                de=StatusOcorrencia.AGUARDANDO_REVISAO,
                para=StatusOcorrencia.EM_ATENDIMENTO,
                em=AGORA,
                por_id=agente_id,
                justificativa="Despacho tático",
            ),
        ],
    )


def test_round_trip_dominio_para_model_e_vice_versa() -> None:
    """Valida a conversão íntegra entre entidade de domínio e modelo relacional em ambas as direções."""
    ocorrencia_original = _criar_ocorrencia_completa()

    model = OcorrenciaMapper.to_model(ocorrencia_original)

    assert model.id == ocorrencia_original.id
    assert model.natureza == "Roubo a Estabelecimento"
    assert len(model.envolvidos) == 2
    assert all(e.ativo for e in model.envolvidos)
    assert len(model.tipificacoes) == 1
    assert model.tipificacoes[0].artigo == "Art. 157 CP"
    assert len(model.evidencias) == 1
    assert len(model.itens_apreendidos) == 1
    assert len(model.itens_apreendidos[0].movimentacoes) == 1
    assert len(model.historico) == 2

    reconstituida = OcorrenciaMapper.to_domain(model)

    assert reconstituida.id == ocorrencia_original.id
    assert reconstituida.natureza == ocorrencia_original.natureza
    assert reconstituida.coordenada == ocorrencia_original.coordenada
    assert len(reconstituida.envolvidos) == 2
    assert len(reconstituida.tipificacoes) == 1
    assert len(reconstituida.evidencias) == 1
    assert len(reconstituida.itens_apreendidos) == 1
    assert len(reconstituida.historico_status) == 2


def test_sincronizacao_envolvidos_soft_delete() -> None:
    """Valida se a remoção de envolvidos na entidade gera exclusão lógica (ativo=False) no modelo (RNF03)."""
    ocorrencia = _criar_ocorrencia_completa()
    model = OcorrenciaMapper.to_model(ocorrencia)

    envolvido_mantido = ocorrencia.envolvidos[0]
    # Removemos o segundo envolvido e adicionamos um novo
    novo_envolvido = Envolvido(id=uuid4(), nome="Testemunha", tipo=TipoEnvolvido.TESTEMUNHA)
    ocorrencia.envolvidos = [envolvido_mantido, novo_envolvido]

    OcorrenciaMapper.atualizar_model(model, ocorrencia)

    # O envolvido mantido continua ativo=True
    m_mantido = next(e for e in model.envolvidos if e.id == envolvido_mantido.id)
    assert m_mantido.ativo is True

    # O envolvido removido do domínio NÃO é deletado; vira ativo=False (RNF03)
    id_removido = [e.id for e in model.envolvidos if e.id not in {envolvido_mantido.id, novo_envolvido.id}][0]
    m_removido = next(e for e in model.envolvidos if e.id == id_removido)
    assert m_removido.ativo is False

    # O novo envolvido é adicionado com ativo=True
    m_novo = next(e for e in model.envolvidos if e.id == novo_envolvido.id)
    assert m_novo.ativo is True
    assert m_novo.nome == "Testemunha"


def test_sincronizacao_append_only_custodia_e_historico() -> None:
    """Valida se movimentações de custódia e histórico de status crescem exclusivamente por anexação."""
    ocorrencia = _criar_ocorrencia_completa()
    model = OcorrenciaMapper.to_model(ocorrencia)

    # Adiciona nova movimentação de custódia ao item
    item = ocorrencia.itens_apreendidos[0]
    nova_mov = MovimentacaoCustodia(
        em=AGORA + timedelta(minutes=10),
        por_id=uuid4(),
        origem="Depósito Central",
        destino="Instituto de Perícias",
        observacao="Encaminhado para perícia balística.",
    )
    item.movimentacoes.append(nova_mov)

    # Adiciona novo registro ao histórico de status
    ocorrencia.historico_status.append(
        RegistroHistoricoStatus(
            de=StatusOcorrencia.EM_ATENDIMENTO,
            para=StatusOcorrencia.VALIDADA,
            em=AGORA + timedelta(minutes=20),
            por_id=uuid4(),
            justificativa="Aprovada pelo Delegado",
        )
    )

    OcorrenciaMapper.atualizar_model(model, ocorrencia)

    assert len(model.itens_apreendidos[0].movimentacoes) == 2
    assert model.itens_apreendidos[0].movimentacoes[1].destino == "Instituto de Perícias"
    assert model.itens_apreendidos[0].movimentacoes[1].ordem == 1

    assert len(model.historico) == 3
    assert model.historico[2].para == StatusOcorrencia.VALIDADA.value
    assert model.historico[2].ordem == 2
