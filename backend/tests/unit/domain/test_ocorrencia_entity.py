"""Testes unitários da entidade Ocorrencia — sem banco, sem servidor (DEC-02/03, RF01*, RF04*, RF14, RF19)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from domain.ocorrencia.entity import (
    Envolvido,
    Evidencia,
    Ocorrencia,
    RegistroHistoricoStatus,
    TipificacaoPenal,
    TipoEnvolvido,
)
from domain.ocorrencia.status import StatusOcorrencia, TRANSICOES
from domain.shared.exceptions import (
    AcessoNegadoError,
    CampoObrigatorioError,
    TransicaoInvalidaError,
    ValorInvalidoError,
)
from domain.shared.geo import Coordenada

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
AGENTE = uuid4()
DELEGADO = uuid4()
OPERADOR = uuid4()


def _envolvido(**kw) -> Envolvido:
    defaults = dict(nome="João Silva", tipo=TipoEnvolvido.VITIMA)
    defaults.update(kw)
    return Envolvido(**defaults)


def _registrar(**kwargs) -> Ocorrencia:
    defaults = dict(
        agente_policial_id=AGENTE,
        natureza="Furto",
        descricao="Furto de veículo na rua X, próximo à praça central.",
        localizacao="Rua das Flores, 123",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=AGORA - timedelta(hours=1),
        numero_protocolo="SGOPI-2026-000001",
        agora=AGORA,
        envolvidos=[_envolvido()],
    )
    defaults.update(kwargs)
    return Ocorrencia.registrar(**defaults)


def _validada() -> Ocorrencia:
    o = _registrar()
    o.validar(DELEGADO, AGORA + timedelta(minutes=5))
    return o


# ------------------------------------------------------------------ factory

def test_registrar_nasce_em_aguardando_revisao():
    o = _registrar()
    assert o.status == StatusOcorrencia.AGUARDANDO_REVISAO
    assert o.numero_protocolo == "SGOPI-2026-000001"
    assert o.versao == 1
    assert o.criada_em == AGORA
    assert o.atualizada_em == AGORA


def test_registrar_grava_historico_inicial():
    o = _registrar()
    assert len(o.historico_status) == 1
    h = o.historico_status[0]
    assert h.de is None and h.para == StatusOcorrencia.AGUARDANDO_REVISAO and h.por_id == AGENTE


def test_registrar_sem_envolvido_e_rejeitado():
    with pytest.raises(CampoObrigatorioError) as exc:
        _registrar(envolvidos=[])
    assert exc.value.chave == "ocorrencia.sem_envolvidos"


def test_descricao_vazia():
    with pytest.raises(CampoObrigatorioError):
        _registrar(descricao="   ")


def test_descricao_curta():
    with pytest.raises(ValorInvalidoError) as exc:
        _registrar(descricao="curta demais")
    assert exc.value.chave == "ocorrencia.descricao_curta"


def test_localizacao_vazia():
    with pytest.raises(CampoObrigatorioError):
        _registrar(localizacao="")


def test_natureza_vazia():
    with pytest.raises(CampoObrigatorioError):
        _registrar(natureza="")


def test_data_fato_futura():
    with pytest.raises(ValorInvalidoError) as exc:
        _registrar(data_hora_fato=AGORA + timedelta(minutes=1))
    assert exc.value.chave == "ocorrencia.data_fato_futura"


def test_data_fato_sem_fuso():
    with pytest.raises(ValorInvalidoError):
        _registrar(data_hora_fato=datetime(2026, 9, 13, 10, 0))


def test_protocolo_vazio():
    with pytest.raises(CampoObrigatorioError):
        _registrar(numero_protocolo="")


def test_coordenada_invalida_na_factory():
    with pytest.raises(ValorInvalidoError):
        _registrar(coordenada=Coordenada(95, 0))


# --------------------------------------------------------------- envolvidos

def test_adicionar_envolvido():
    o = _registrar()
    o.adicionar_envolvido(_envolvido(nome="Maria", tipo=TipoEnvolvido.TESTEMUNHA))
    assert len(o.envolvidos) == 2


def test_adicionar_envolvido_duplicado():
    o = _registrar()
    e = o.envolvidos[0]
    with pytest.raises(ValorInvalidoError):
        o.adicionar_envolvido(e)


def test_envolvido_nome_vazio():
    with pytest.raises(CampoObrigatorioError):
        _envolvido(nome=" ")


def test_envolvido_cpf_invalido():
    with pytest.raises(ValorInvalidoError):
        _envolvido(documento="123.456.789-00")


def test_envolvido_cpf_valido():
    assert _envolvido(documento="123.456.789-09").documento == "123.456.789-09"


def test_tipificacao_campos_obrigatorios():
    with pytest.raises(CampoObrigatorioError):
        TipificacaoPenal(artigo="", descricao="x")


# --------------------------------------------------------------- evidências

def _evidencia(**kw) -> Evidencia:
    defaults = dict(
        nome_original="foto.png",
        formato="png",
        tamanho=8,
        hash_sha256="a" * 64,
        chave_armazenamento="abc.png",
        enviada_em=AGORA,
    )
    defaults.update(kw)
    return Evidencia(**defaults)


def test_adicionar_evidencia_e_append_only():
    o = _registrar()
    o.adicionar_evidencia(_evidencia(), AGENTE, AGORA + timedelta(minutes=1))
    assert [e.nome_original for e in o.evidencias] == ["foto.png"]
    assert o.versao == 2


def test_evidencia_exige_autor_e_status_editavel():
    o = _registrar()
    with pytest.raises(AcessoNegadoError):
        o.adicionar_evidencia(_evidencia(), uuid4(), AGORA)
    o.validar(DELEGADO, AGORA)
    with pytest.raises(TransicaoInvalidaError) as exc:
        o.adicionar_evidencia(_evidencia(), AGENTE, AGORA)
    assert exc.value.chave == "evidencia.status_invalido"


def test_evidencia_valida_metadados():
    with pytest.raises(ValorInvalidoError):
        _evidencia(tamanho=0)
    with pytest.raises(ValorInvalidoError):
        _evidencia(hash_sha256="invalido")


# --------------------------------------------------------------- transições

def test_tabela_de_transicoes_tem_seis_arestas():
    assert len(TRANSICOES) == 6


def test_validar_congela_narrativa_e_registra_delegado():
    o = _registrar()
    em = AGORA + timedelta(minutes=5)
    o.validar(DELEGADO, em)
    assert o.status == StatusOcorrencia.VALIDADA
    assert o.validada_por_id == DELEGADO
    assert o.hash_narrativa is not None and len(o.hash_narrativa) == 64
    assert o.narrativa_integra() is True
    assert o.versao == 2 and o.atualizada_em == em
    assert o.historico_status[-1] == RegistroHistoricoStatus(
        de=StatusOcorrencia.AGUARDANDO_REVISAO, para=StatusOcorrencia.VALIDADA, em=em, por_id=DELEGADO
    )


def test_narrativa_integra_detecta_adulteracao():
    o = _validada()
    o.descricao = "narrativa adulterada depois da validação, muito longa"
    assert o.narrativa_integra() is False


def test_narrativa_integra_none_antes_de_validar():
    assert _registrar().narrativa_integra() is None


def test_devolver_para_correcao_exige_justificativa():
    o = _registrar()
    with pytest.raises(ValorInvalidoError) as exc:
        o.devolver_para_correcao(DELEGADO, "curta", AGORA)
    assert exc.value.chave == "ocorrencia.justificativa_curta"
    assert o.status == StatusOcorrencia.AGUARDANDO_REVISAO


def test_devolver_para_correcao():
    o = _registrar()
    o.devolver_para_correcao(DELEGADO, "Faltam dados do veículo.", AGORA)
    assert o.status == StatusOcorrencia.EM_CORRECAO
    assert o.justificativa_revisao == "Faltam dados do veículo."
    assert o.historico_status[-1].justificativa == "Faltam dados do veículo."


def test_rejeitar_e_terminal():
    o = _registrar()
    o.rejeitar(DELEGADO, "Fato atípico, não configura crime.", AGORA)
    assert o.status == StatusOcorrencia.REJEITADA
    with pytest.raises(TransicaoInvalidaError):
        o.reenviar(AGENTE, AGORA)
    with pytest.raises(TransicaoInvalidaError):
        o.validar(DELEGADO, AGORA)


def test_rejeitar_exige_justificativa():
    with pytest.raises(ValorInvalidoError):
        _registrar().rejeitar(DELEGADO, "", AGORA)


def test_validar_fora_de_aguardando_revisao():
    o = _validada()
    with pytest.raises(TransicaoInvalidaError) as exc:
        o.validar(DELEGADO, AGORA)
    assert exc.value.detalhes["status_atual"] == "VALIDADA"


def test_corrigir_so_em_correcao():
    o = _registrar()
    with pytest.raises(TransicaoInvalidaError):
        o.corrigir(AGENTE, AGORA, descricao="Nova descrição bem detalhada dos fatos.")


def test_corrigir_so_pelo_autor():
    o = _registrar()
    o.devolver_para_correcao(DELEGADO, "Complementar narrativa.", AGORA)
    with pytest.raises(AcessoNegadoError):
        o.corrigir(uuid4(), AGORA, descricao="Nova descrição bem detalhada dos fatos.")


def test_ciclo_correcao_reenvio_validacao():
    o = _registrar()
    o.devolver_para_correcao(DELEGADO, "Complementar narrativa.", AGORA)
    o.corrigir(
        AGENTE,
        AGORA + timedelta(minutes=1),
        descricao="Descrição complementada com placa do veículo ABC-1234.",
        coordenada=Coordenada(-29.70, -55.70),
        envolvidos=[_envolvido(nome="Ana", tipo=TipoEnvolvido.TESTEMUNHA)],
    )
    assert o.coordenada == Coordenada(-29.70, -55.70)
    assert o.envolvidos[0].nome == "Ana"
    assert o.status == StatusOcorrencia.EM_CORRECAO
    o.reenviar(AGENTE, AGORA + timedelta(minutes=2))
    assert o.status == StatusOcorrencia.AGUARDANDO_REVISAO
    o.validar(DELEGADO, AGORA + timedelta(minutes=3))
    assert o.status == StatusOcorrencia.VALIDADA
    assert [h.para for h in o.historico_status] == [
        StatusOcorrencia.AGUARDANDO_REVISAO,
        StatusOcorrencia.EM_CORRECAO,
        StatusOcorrencia.AGUARDANDO_REVISAO,
        StatusOcorrencia.VALIDADA,
    ]
    assert o.versao == 5


def test_corrigir_nao_aceita_zero_envolvidos():
    o = _registrar()
    o.devolver_para_correcao(DELEGADO, "Complementar narrativa.", AGORA)
    with pytest.raises(CampoObrigatorioError):
        o.corrigir(AGENTE, AGORA, envolvidos=[])


def test_reenviar_so_pelo_autor():
    o = _registrar()
    o.devolver_para_correcao(DELEGADO, "Complementar narrativa.", AGORA)
    with pytest.raises(AcessoNegadoError):
        o.reenviar(uuid4(), AGORA)


def test_despachar_e_encerrar():
    o = _validada()
    o.despachar(OPERADOR, AGORA + timedelta(minutes=10))
    assert o.status == StatusOcorrencia.EM_ATENDIMENTO
    o.encerrar(OPERADOR, "Suspeito conduzido à delegacia.", AGORA + timedelta(hours=1))
    assert o.status == StatusOcorrencia.ENCERRADA
    assert o.desfecho == "Suspeito conduzido à delegacia."


def test_despachar_exige_validada():
    with pytest.raises(TransicaoInvalidaError):
        _registrar().despachar(OPERADOR, AGORA)


def test_encerrar_exige_desfecho():
    o = _validada()
    o.despachar(OPERADOR, AGORA)
    with pytest.raises(CampoObrigatorioError):
        o.encerrar(OPERADOR, "  ", AGORA)
    assert o.status == StatusOcorrencia.EM_ATENDIMENTO


def test_encerrada_e_terminal():
    o = _validada()
    o.despachar(OPERADOR, AGORA)
    o.encerrar(OPERADOR, "Atendido.", AGORA)
    with pytest.raises(TransicaoInvalidaError):
        o.despachar(OPERADOR, AGORA)
