"""Testes unitários da entidade Ocorrencia — sem banco, sem servidor."""
import pytest
from uuid import uuid4

from domain.ocorrencia.entity import (
    Envolvido,
    Ocorrencia,
    StatusOcorrencia,
    TipificacaoPenal,
    TipoEnvolvido,
)
from domain.shared.exceptions import TransicaoInvalidaError


def _ocorrencia_valida(**kwargs) -> Ocorrencia:
    defaults = dict(
        agente_policial_id=uuid4(),
        natureza="Furto",
        descricao="Furto de veículo na rua X",
        localizacao="Rua das Flores, 123",
    )
    defaults.update(kwargs)
    return Ocorrencia(**defaults)


def test_cria_ocorrencia_gera_protocolo():
    o = _ocorrencia_valida()
    assert o.numero_protocolo is not None
    assert o.numero_protocolo.startswith("SGOPI-")


def test_status_inicial_e_registrada():
    o = _ocorrencia_valida()
    assert o.status == StatusOcorrencia.REGISTRADA


def test_descricao_vazia_levanta_valueerror():
    with pytest.raises(ValueError, match="descrição"):
        _ocorrencia_valida(descricao="   ")


def test_localizacao_vazia_levanta_valueerror():
    with pytest.raises(ValueError, match="localização"):
        _ocorrencia_valida(localizacao="")


def test_transicao_registrada_para_em_validacao():
    o = _ocorrencia_valida()
    o.enviar_para_validacao()
    assert o.status == StatusOcorrencia.EM_VALIDACAO


def test_transicao_invalida_direto_para_validada():
    o = _ocorrencia_valida()
    with pytest.raises(TransicaoInvalidaError):
        o.validar(uuid4())


def test_validar_muda_status_e_registra_delegado():
    o = _ocorrencia_valida()
    delegado_id = uuid4()
    o.enviar_para_validacao()
    o.validar(delegado_id)
    assert o.status == StatusOcorrencia.VALIDADA
    assert o.validada_por_id == delegado_id


def test_rejeitar_muda_status_e_registra_delegado():
    o = _ocorrencia_valida()
    delegado_id = uuid4()
    o.enviar_para_validacao()
    o.rejeitar(delegado_id)
    assert o.status == StatusOcorrencia.REJEITADA
    assert o.validada_por_id == delegado_id


def test_adicionar_envolvido():
    o = _ocorrencia_valida()
    e = Envolvido(nome="João Silva", tipo=TipoEnvolvido.VITIMA)
    o.adicionar_envolvido(e)
    assert len(o.envolvidos) == 1
    assert o.envolvidos[0].nome == "João Silva"


def test_adicionar_envolvido_duplicado_levanta_valueerror():
    o = _ocorrencia_valida()
    e = Envolvido(nome="João Silva", tipo=TipoEnvolvido.VITIMA)
    o.adicionar_envolvido(e)
    with pytest.raises(ValueError, match="já foi adicionado"):
        o.adicionar_envolvido(e)


def test_tipificacao_adicionada():
    o = _ocorrencia_valida()
    o.tipificacoes.append(TipificacaoPenal(artigo="Art. 155 CP", descricao="Furto simples"))
    assert len(o.tipificacoes) == 1
