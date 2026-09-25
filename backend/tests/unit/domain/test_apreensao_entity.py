"""Testes unitários de ItemApreendido, MovimentacaoCustodia e das operações de apreensão do agregado (RF03 / UC03)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from domain.ocorrencia.apreensao import EstadoConservacao, ItemApreendido, MovimentacaoCustodia, TipoItemApreendido, UnidadeMedida
from domain.ocorrencia.status import ESTADOS_ACEITAM_APREENSAO, StatusOcorrencia
from domain.shared.exceptions import (
    AcessoNegadoError,
    CampoObrigatorioError,
    ConflitoError,
    EntidadeNaoEncontradaError,
    TransicaoInvalidaError,
    ValorInvalidoError,
)
from tests.unit.domain.test_ocorrencia_entity import AGENTE, AGORA, DELEGADO, _registrar

DEPOIS = AGORA + timedelta(minutes=10)


def _item(**kw) -> ItemApreendido:
    defaults = dict(
        tipo=TipoItemApreendido.OBJETO,
        descricao="Aparelho celular Samsung preto",
        quantidade=1,
        estado_conservacao=EstadoConservacao.BOM,
        numero_lacre="lacre-0001",
        localizacao_deposito="Cofre 2 — prateleira A",
        registrado_em=AGORA,
        registrado_por_id=AGENTE,
    )
    defaults.update(kw)
    return ItemApreendido(**defaults)


# ------------------------------------------------------------- ItemApreendido

def test_item_normaliza_campos_e_abre_cadeia_de_custodia_com_recebimento():
    item = _item(numero_lacre="  lacre-0001 ", numero_serie=" abc123 ", marca="  ", calibre=None)
    assert item.numero_lacre == "LACRE-0001" and item.numero_serie == "ABC123" and item.marca is None
    assert item.unidade is UnidadeMedida.UNIDADE
    assert len(item.movimentacoes) == 1
    assert item.movimentacoes[0].origem is None and item.movimentacoes[0].destino == "Cofre 2 — prateleira A"
    assert item.movimentacoes[0].por_id == AGENTE and item.localizacao_atual == "Cofre 2 — prateleira A"


@pytest.mark.parametrize(
    ("campos", "excecao", "chave"),
    [
        ({"descricao": "  "}, CampoObrigatorioError, "apreensao.descricao_vazia"),
        ({"quantidade": 0}, ValorInvalidoError, "apreensao.quantidade_invalida"),
        ({"numero_lacre": ""}, CampoObrigatorioError, "apreensao.lacre_vazio"),
        ({"localizacao_deposito": " "}, CampoObrigatorioError, "apreensao.localizacao_vazia"),
        ({"registrado_em": datetime(2026, 9, 13, 12, 0)}, ValorInvalidoError, "apreensao.data_sem_fuso"),
        ({"tipo": TipoItemApreendido.ARMA_DE_FOGO, "marca": "Taurus"}, CampoObrigatorioError, "apreensao.arma_sem_calibre_ou_marca"),
        ({"tipo": TipoItemApreendido.ARMA_DE_FOGO, "calibre": ".38"}, CampoObrigatorioError, "apreensao.arma_sem_calibre_ou_marca"),
    ],
)
def test_item_rejeita_campos_invalidos(campos, excecao, chave):
    with pytest.raises(excecao) as exc:
        _item(**campos)
    assert exc.value.chave == chave


def test_arma_de_fogo_com_calibre_e_marca_e_aceita_sem_serie():
    item = _item(tipo=TipoItemApreendido.ARMA_DE_FOGO, marca="Taurus", calibre=".38", numero_serie=None)
    assert item.calibre == ".38" and item.numero_serie is None


def test_entorpecente_em_gramas():
    item = _item(tipo=TipoItemApreendido.ENTORPECENTE, descricao="Substância análoga à cocaína", quantidade=250, unidade=UnidadeMedida.GRAMA)
    assert item.quantidade == 250 and item.unidade is UnidadeMedida.GRAMA


# ------------------------------------------------------ MovimentacaoCustodia

def test_movimentar_encadeia_origem_com_localizacao_atual():
    item = _item()
    m = item.movimentar(DELEGADO, " Depósito central — caixa 7 ", "transferência para perícia", DEPOIS)
    assert m.origem == "Cofre 2 — prateleira A" and m.destino == "Depósito central — caixa 7"
    assert m.observacao == "transferência para perícia" and item.localizacao_atual == m.destino
    assert [x.destino for x in item.movimentacoes] == ["Cofre 2 — prateleira A", "Depósito central — caixa 7"]


def test_movimentar_rejeita_destino_vazio_igual_ou_retroativo():
    item = _item()
    with pytest.raises(CampoObrigatorioError) as exc:
        item.movimentar(DELEGADO, "  ", None, DEPOIS)
    assert exc.value.chave == "apreensao.destino_vazio"
    with pytest.raises(ValorInvalidoError) as exc:
        item.movimentar(DELEGADO, "Cofre 2 — prateleira A", None, DEPOIS)
    assert exc.value.chave == "apreensao.destino_igual_origem"
    with pytest.raises(ValorInvalidoError) as exc:
        item.movimentar(DELEGADO, "Outro lugar", None, AGORA - timedelta(seconds=1))
    assert exc.value.chave == "apreensao.movimentacao_retroativa"
    assert len(item.movimentacoes) == 1


def test_movimentacao_exige_fuso():
    with pytest.raises(ValorInvalidoError) as exc:
        MovimentacaoCustodia(em=datetime(2026, 9, 13), por_id=AGENTE, origem=None, destino="X")
    assert exc.value.chave == "apreensao.data_sem_fuso"


# ---------------------------------------------------- Ocorrencia.registrar_apreensao

def test_registrar_apreensao_vincula_item_e_incrementa_versao():
    o = _registrar()
    versao = o.versao
    o.registrar_apreensao(_item(), AGENTE, DEPOIS)
    assert len(o.itens_apreendidos) == 1 and o.versao == versao + 1 and o.atualizada_em == DEPOIS
    assert o.item_apreendido(o.itens_apreendidos[0].id).numero_lacre == "LACRE-0001"


def test_registrar_apreensao_nao_altera_hash_da_narrativa_validada():
    o = _registrar()
    o.validar(DELEGADO, AGORA + timedelta(minutes=1))
    o.registrar_apreensao(_item(), AGENTE, DEPOIS)
    assert o.status is StatusOcorrencia.VALIDADA and o.narrativa_integra() is True


def test_somente_autor_registra_apreensao():
    o = _registrar()
    with pytest.raises(AcessoNegadoError):
        o.registrar_apreensao(_item(), uuid4(), DEPOIS)
    assert o.itens_apreendidos == []


@pytest.mark.parametrize("status", [s for s in StatusOcorrencia if s not in ESTADOS_ACEITAM_APREENSAO])
def test_status_fora_do_fluxo_nao_aceita_apreensao(status):
    o = _registrar()
    o.status = status
    with pytest.raises(TransicaoInvalidaError) as exc:
        o.registrar_apreensao(_item(), AGENTE, DEPOIS)
    assert exc.value.chave == "apreensao.status_invalido"


@pytest.mark.parametrize("status", sorted(ESTADOS_ACEITAM_APREENSAO, key=lambda s: s.value))
def test_status_registrada_ou_em_andamento_aceita_apreensao(status):
    o = _registrar()
    o.status = status
    o.registrar_apreensao(_item(), AGENTE, DEPOIS)
    assert len(o.itens_apreendidos) == 1


def test_lacre_duplicado_no_agregado_e_conflito():
    o = _registrar()
    o.registrar_apreensao(_item(numero_lacre="L-1"), AGENTE, DEPOIS)
    with pytest.raises(ConflitoError) as exc:
        o.registrar_apreensao(_item(numero_lacre=" l-1 "), AGENTE, DEPOIS)
    assert exc.value.chave == "apreensao.lacre_duplicado" and exc.value.detalhes["numero_lacre"] == "L-1"


def test_item_duplicado_por_id_e_rejeitado():
    o = _registrar()
    item = _item()
    o.registrar_apreensao(item, AGENTE, DEPOIS)
    with pytest.raises(ValorInvalidoError) as exc:
        o.registrar_apreensao(item, AGENTE, DEPOIS)
    assert exc.value.chave == "apreensao.duplicada"


# ------------------------------------------- Ocorrencia.movimentar_item_apreendido

def test_movimentar_item_do_agregado_toca_versao():
    o = _registrar()
    item = _item()
    o.registrar_apreensao(item, AGENTE, DEPOIS)
    versao = o.versao
    m = o.movimentar_item_apreendido(item.id, DELEGADO, "Cofre da delegacia", None, DEPOIS + timedelta(hours=1))
    assert m.origem == item.localizacao_deposito and o.versao == versao + 1
    assert o.item_apreendido(item.id).localizacao_atual == "Cofre da delegacia"


def test_movimentar_item_inexistente_404():
    o = _registrar()
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        o.movimentar_item_apreendido(uuid4(), DELEGADO, "X", None, DEPOIS)
    assert exc.value.chave == "apreensao.not_found"


def test_ocorrencia_excluida_nao_aceita_movimentacao():
    o = _registrar()
    item = _item()
    o.registrar_apreensao(item, AGENTE, DEPOIS)
    o.excluir(DELEGADO, "registro em duplicidade", DEPOIS)
    with pytest.raises(TransicaoInvalidaError):
        o.movimentar_item_apreendido(item.id, DELEGADO, "X", None, DEPOIS + timedelta(hours=1))


# ------------------------------------------ Ocorrencia.registrar(itens_apreendidos=...)

def test_factory_aceita_itens_apreendidos_opcionais_sem_tocar_versao():
    o = _registrar(itens_apreendidos=[_item(numero_lacre="L-1"), _item(numero_lacre="L-2")])
    assert [i.numero_lacre for i in o.itens_apreendidos] == ["L-1", "L-2"]
    assert o.versao == 1 and o.status is StatusOcorrencia.AGUARDANDO_REVISAO
    assert _registrar().itens_apreendidos == [] and _registrar(itens_apreendidos=None).itens_apreendidos == []


def test_factory_rejeita_lacre_repetido_no_mesmo_registro():
    with pytest.raises(ConflitoError) as exc:
        _registrar(itens_apreendidos=[_item(numero_lacre="L-1"), _item(numero_lacre="l-1")])
    assert exc.value.chave == "apreensao.lacre_duplicado"
