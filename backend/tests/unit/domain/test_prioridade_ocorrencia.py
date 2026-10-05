"""Sugestão #7: regra de sugestão de prioridade e redefinição pelo Delegado (domínio puro)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipificacaoPenal, TipoEnvolvido
from domain.ocorrencia.prioridade import PrioridadeOcorrencia as P
from domain.ocorrencia.prioridade import interpretar_prioridade, sugerir_prioridade
from domain.shared.exceptions import TransicaoInvalidaError, ValorInvalidoError
from domain.shared.geo import Coordenada

AGORA = datetime(2026, 10, 5, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    ("natureza", "tipificacoes", "esperada"),
    [
        ("Homicídio", (), P.URGENTE),
        ("Roubo a pedestre", (), P.ALTA),
        ("Furto", (), P.MEDIA),
        ("Perda ou Extravio de Documento/Objeto", (), P.BAIXA),
        ("Acidente de Trânsito sem Vítima", (), P.BAIXA),
        ("Theft / Larceny", (), P.MEDIA),
        ("Furto", ("Art. 157 CP Roubo",), P.ALTA),  # a tipificação mais grave prevalece
        ("Outro Fato Circunstanciado", ("Art. 121 CP Homicídio",), P.URGENTE),
    ],
)
def test_sugestao_pela_natureza_e_tipificacoes(natureza, tipificacoes, esperada):
    assert sugerir_prioridade(natureza, tipificacoes) == esperada


def test_pesos_ordenam_da_mais_grave_para_a_mais_leve():
    assert sorted(P, key=lambda p: p.peso, reverse=True) == [P.URGENTE, P.ALTA, P.MEDIA, P.BAIXA]


def test_interpretar_prioridade():
    assert interpretar_prioridade(" urgente ") == P.URGENTE
    assert interpretar_prioridade("") is None and interpretar_prioridade(None) is None
    with pytest.raises(ValorInvalidoError) as exc:
        interpretar_prioridade("XPTO")
    assert exc.value.chave == "ocorrencia.prioridade_invalida"


def _ocorrencia(**kw) -> Ocorrencia:
    base = dict(
        agente_policial_id=uuid4(),
        natureza="Furto",
        descricao="Furto de bicicleta em frente ao mercado central.",
        localizacao="Rua A, 1",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="OC-1",
        agora=AGORA,
        envolvidos=[Envolvido(nome="Maria", tipo=TipoEnvolvido.VITIMA)],
    )
    base.update(kw)
    return Ocorrencia.registrar(**base)


def test_registro_sugere_ou_respeita_o_ajuste_do_agente():
    assert _ocorrencia().prioridade == P.MEDIA
    assert _ocorrencia(tipificacoes=[TipificacaoPenal("Art. 157", "Roubo")]).prioridade == P.ALTA
    assert _ocorrencia(prioridade=P.URGENTE).prioridade == P.URGENTE


def test_redefinir_exige_justificativa_mudanca_e_status_em_fluxo():
    o = _ocorrencia()
    with pytest.raises(ValorInvalidoError):
        o.redefinir_prioridade(P.ALTA, "curta", AGORA)
    with pytest.raises(ValorInvalidoError) as exc:
        o.redefinir_prioridade(P.MEDIA, "Sem mudança nenhuma aqui.", AGORA)
    assert exc.value.chave == "ocorrencia.prioridade_inalterada"
    versao = o.versao
    assert o.redefinir_prioridade(P.URGENTE, "Suspeito ainda no local.", AGORA + timedelta(minutes=1)) == P.MEDIA
    assert o.prioridade == P.URGENTE and o.versao == versao + 1 and o.atualizada_em == AGORA + timedelta(minutes=1)
    o.rejeitar(uuid4(), "Fato atípico, sem materialidade.", AGORA)
    with pytest.raises(TransicaoInvalidaError):
        o.redefinir_prioridade(P.BAIXA, "Ocorrência já rejeitada.", AGORA)
