"""Regra de sigilo dos ofícios interagências (RF10): quem pode ler cada nível."""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from domain.interagencias.entity import ComunicacaoInteragencias, NivelSigilo, niveis_sigilo_visiveis
from domain.usuario.entity import Papel

AGORA = datetime(2026, 11, 9, 10, 0, tzinfo=UTC)


def _oficio(nivel: NivelSigilo, remetente=None) -> ComunicacaoInteragencias:
    return ComunicacaoInteragencias.criar(
        numero_oficio="OFI-2026-000001",
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=["POLICIA_MILITAR"],
        remetente_id=remetente or uuid4(),
        assunto="Pedido de apoio tático",
        corpo="Solicita-se apoio de duas guarnições na operação.",
        nivel_sigilo=nivel,
        instante=AGORA,
    )


@pytest.mark.parametrize(
    ("papel", "esperado"),
    [
        (Papel.DELEGADO, {NivelSigilo.PADRAO, NivelSigilo.RESERVADO, NivelSigilo.CONFIDENCIAL}),
        (Papel.SUPERVISOR, {NivelSigilo.PADRAO, NivelSigilo.RESERVADO, NivelSigilo.CONFIDENCIAL}),
        (Papel.ESCRIVAO, {NivelSigilo.PADRAO, NivelSigilo.RESERVADO}),
        (Papel.OPERADOR_CENTRAL, {NivelSigilo.PADRAO, NivelSigilo.RESERVADO}),
        (Papel.AGENTE, {NivelSigilo.PADRAO}),
        (Papel.PERITO, {NivelSigilo.PADRAO}),
    ],
)
def test_niveis_visiveis_por_papel(papel, esperado):
    assert niveis_sigilo_visiveis(papel) == esperado


def test_confidencial_invisivel_para_operador():
    assert not _oficio(NivelSigilo.CONFIDENCIAL).visivel_para(Papel.OPERADOR_CENTRAL, uuid4())


def test_remetente_sempre_le_o_proprio_oficio():
    remetente = uuid4()
    assert _oficio(NivelSigilo.CONFIDENCIAL, remetente).visivel_para(Papel.AGENTE, remetente)


def test_padrao_visivel_para_qualquer_papel():
    assert _oficio(NivelSigilo.PADRAO).visivel_para(Papel.PERITO, uuid4())
