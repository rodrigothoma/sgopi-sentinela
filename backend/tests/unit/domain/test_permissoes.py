"""Catálogo de permissões (RNF02): fixa quem pode o quê, para que uma mudança de acesso seja deliberada."""
from uuid import uuid4

import pytest

from application.ports.inbound.ator import Ator
from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel
from domain.usuario.permissoes import PAPEIS_POR_PERMISSAO, Permissao, papeis_com

D, S, OP, A, E, P = "DELEGADO", "SUPERVISOR", "OPERADOR_CENTRAL", "AGENTE", "ESCRIVAO", "PERITO"

ESPERADO = {
    Permissao.CONSULTAR_OCORRENCIAS: {A, D, OP, S},
    Permissao.EXPORTAR_REGISTROS: {D, S},
    Permissao.CONSULTAR_AUDITORIA: {D, S},
    Permissao.CONSULTAR_USUARIOS: {A, D, OP, S},
    Permissao.GERIR_USUARIOS: {S, OP},
    Permissao.CONSULTAR_INDICADORES: {D, S, OP},
    Permissao.CONSULTAR_FROTA: {OP, S, D, A},
    Permissao.GERIR_FROTA: {OP, S},
    Permissao.DESPACHAR_VIATURA: {OP, S},
    Permissao.ACOMPANHAR_ATENDIMENTO: {OP, S, D},
    Permissao.CONSULTAR_INQUERITOS: {D, S, OP},
    Permissao.GERIR_INQUERITOS: {D},
    Permissao.CONSULTAR_LAUDOS: {D, P, S, OP, A},
    Permissao.SOLICITAR_LAUDO: {D, P},
    Permissao.ANEXAR_LAUDO: {P, D},
    Permissao.CONSULTAR_MEDIDAS: {S, D, A, OP, E},
    Permissao.GERIR_MEDIDAS: {D},
    Permissao.VERIFICAR_VENCIMENTOS_MEDIDAS: {D, S, OP},
    Permissao.ALERTAR_VENCIMENTO_MEDIDA: {D, S, OP, A},
    Permissao.ENVIAR_OFICIO: {D, S, E, OP},
    Permissao.EMITIR_ALERTA_TATICO: {S, D, OP},
    Permissao.DAR_CIENCIA_ALERTA: {S, D},
}


def test_toda_permissao_tem_papeis_definidos():
    assert set(PAPEIS_POR_PERMISSAO) == set(Permissao)


@pytest.mark.parametrize("permissao", list(Permissao))
def test_catalogo_de_papeis(permissao):
    assert {p.value for p in PAPEIS_POR_PERMISSAO[permissao]} == ESPERADO[permissao]


def test_cidadao_nao_tem_nenhuma_permissao():
    assert not any(Papel.CIDADAO in papeis for papeis in PAPEIS_POR_PERMISSAO.values())


def test_papeis_com_segue_ordem_do_enum():
    assert papeis_com(Permissao.ENVIAR_OFICIO) == (Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR, Papel.ESCRIVAO)


def test_exigir_preserva_mensagem_e_chave_do_caso_de_uso():
    agente = Ator(id=uuid4(), login="agente", papel=Papel.AGENTE)

    with pytest.raises(AcessoNegadoError) as erro:
        agente.exigir(Permissao.GERIR_MEDIDAS, "Apenas o Delegado.", chave="medida.apenas_delegado")

    assert erro.value.chave == "medida.apenas_delegado"
    assert erro.value.detalhes["exigido"] == ["DELEGADO"]


def test_exigir_sem_mensagem_usa_chave_padrao():
    with pytest.raises(AcessoNegadoError) as erro:
        Ator(id=uuid4(), login="perito", papel=Papel.PERITO).exigir(Permissao.GERIR_FROTA)

    assert erro.value.chave == "auth.forbidden"
