"""Testes unitários puros do UsuarioMapper (sem banco de dados)."""
from uuid import uuid4

from adapters.outbound.persistence.mappers import UsuarioMapper
from domain.usuario.entity import Papel, Usuario
from infrastructure.database.models import UsuarioModel


def test_usuario_to_model_e_to_domain_roundtrip() -> None:
    user_id = uuid4()
    usuario = Usuario(
        id=user_id,
        nome="Agente Silva",
        login="agente.silva",
        senha_hash="hash_seguro_123",
        papel=Papel.AGENTE,
        ativo=True,
    )

    model = UsuarioMapper.to_model(usuario)

    assert model.id == user_id
    assert model.nome == "Agente Silva"
    assert model.login == "agente.silva"
    assert model.senha_hash == "hash_seguro_123"
    assert model.papel == "AGENTE"
    assert model.ativo is True

    reconstituido = UsuarioMapper.to_domain(model)

    assert reconstituido.id == user_id
    assert reconstituido.nome == "Agente Silva"
    assert reconstituido.login == "agente.silva"
    assert reconstituido.papel == Papel.AGENTE
    assert reconstituido.ativo is True


def test_usuario_atualizar_model() -> None:
    user_id = uuid4()
    model = UsuarioModel(
        id=user_id,
        nome="Nome Antigo",
        login="login.antigo",
        senha_hash="senha_antiga",
        papel="AGENTE",
        ativo=True,
    )

    usuario_atualizado = Usuario(
        id=user_id,
        nome="Nome Atualizado",
        login="login.novo",
        senha_hash="senha_nova_hash",
        papel=Papel.DELEGADO,
        ativo=False,
    )

    UsuarioMapper.atualizar_model(model, usuario_atualizado)

    assert model.nome == "Nome Atualizado"
    assert model.login == "login.novo"
    assert model.senha_hash == "senha_nova_hash"
    assert model.papel == "DELEGADO"
    assert model.ativo is False


def test_usuario_roundtrip_de_usuario_inativo() -> None:
    usuario = Usuario(nome="Perita Souza", login="perita.souza", senha_hash="hash", papel=Papel.PERITO, ativo=False)

    assert UsuarioMapper.to_domain(UsuarioMapper.to_model(usuario)) == usuario
