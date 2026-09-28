"""ProvedorTokenJose: emissão/decodificação, expiração e assinatura (RNF02*)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from adapters.outbound.seguranca.hasher_argon2 import HasherArgon2
from adapters.outbound.seguranca.provedor_token_jose import ProvedorTokenJose
from domain.shared.exceptions import CredenciaisInvalidasError
from domain.usuario.entity import Papel

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def test_emitir_e_decodificar():
    p = ProvedorTokenJose("segredo", validade_horas=8)
    uid = uuid4()
    token, expira = p.emitir(uid, "agente", Papel.AGENTE, AGORA)
    assert expira == AGORA + timedelta(hours=8)
    dados = p.decodificar(token, AGORA + timedelta(hours=7))
    assert dados.usuario_id == uid and dados.papel == Papel.AGENTE and dados.login == "agente"


def test_token_expirado():
    p = ProvedorTokenJose("segredo", validade_horas=8)
    token, _ = p.emitir(uuid4(), "a", Papel.AGENTE, AGORA)
    with pytest.raises(CredenciaisInvalidasError):
        p.decodificar(token, AGORA + timedelta(hours=8))


def test_assinatura_com_outro_segredo_e_rejeitada():
    token, _ = ProvedorTokenJose("um").emitir(uuid4(), "a", Papel.AGENTE, AGORA)
    with pytest.raises(CredenciaisInvalidasError):
        ProvedorTokenJose("outro").decodificar(token, AGORA)


def test_token_lixo():
    with pytest.raises(CredenciaisInvalidasError):
        ProvedorTokenJose("x").decodificar("nao.e.jwt", AGORA)


def test_argon2_hash_e_verificacao():
    h = HasherArgon2()
    hash_ = h.gerar_hash("Senha@123")
    assert hash_.startswith("$argon2id$") and "Senha@123" not in hash_
    assert h.verificar("Senha@123", hash_) and not h.verificar("outra", hash_) and not h.verificar("x", "lixo")
