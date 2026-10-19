"""Sugestão #13: gestão do efetivo pelo Supervisor — sem DELETE, sem agir sobre si mesmo, tudo auditado."""
from uuid import UUID, uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_usuarios import (
    AlterarPapelInput,
    AlterarSituacaoUsuarioInput,
    CadastrarUsuarioInput,
)
from application.use_cases.usuario.gerir_usuarios import (
    AlterarPapelUsuario,
    CadastrarUsuario,
    DesativarUsuario,
    ListarUsuariosGestao,
    ReativarUsuario,
)
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError, ValorInvalidoError
from domain.usuario.entity import Papel, Usuario
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR
from tests.fakes.auth_fake import HasherFake, RepositorioUsuarioFake

SUPERVISOR = Ator(id=UUID("00000000-0000-0000-0000-000000000005"), login="supervisor", papel=Papel.SUPERVISOR, ip="10.0.0.1")


@pytest.fixture
def usuarios():
    return RepositorioUsuarioFake()


@pytest.fixture
def gestao(usuarios, uow, relogio, auditoria):
    return (usuarios, uow, relogio, auditoria)


async def _cadastrar(gestao, **kw) -> object:
    dados = dict(nome="Ana Souza", login="Ana.Souza", senha="Senha@123", papel="agente") | kw
    return await CadastrarUsuario(*gestao, HasherFake()).executar(SUPERVISOR, CadastrarUsuarioInput(**dados))


async def test_cadastrar_normaliza_login_guarda_hash_e_audita(gestao, usuarios, auditoria):
    out = await _cadastrar(gestao)
    assert out.login == "ana.souza" and out.papel == "AGENTE" and out.ativo
    salvo = await usuarios.buscar_por_id(out.id)
    assert salvo.senha_hash != "Senha@123"
    registro = auditoria.registros[-1]
    assert registro.operacao == "usuario.cadastrar" and registro.dados_antes is None
    assert registro.dados_depois == {"login": "ana.souza", "nome": "Ana Souza", "papel": "AGENTE", "ativo": True}
    assert "senha" not in str(registro.dados_depois).lower()


@pytest.mark.parametrize(
    ("kw", "chave"),
    [
        ({"senha": "curta"}, "usuario.senha_curta"),
        ({"login": "a b"}, "usuario.login_invalido"),
        ({"papel": "CIDADAO"}, "usuario.papel_invalido"),
        ({"papel": "XPTO"}, "usuario.papel_invalido"),
    ],
)
async def test_cadastrar_valida_entrada(gestao, kw, chave):
    with pytest.raises(ValorInvalidoError) as exc:
        await _cadastrar(gestao, **kw)
    assert exc.value.chave == chave


async def test_login_duplicado_e_somente_supervisor(gestao):
    await _cadastrar(gestao)
    with pytest.raises(ConflitoError):
        await _cadastrar(gestao, login="ANA.SOUZA")
    with pytest.raises(AcessoNegadoError):
        await CadastrarUsuario(*gestao, HasherFake()).executar(
            DELEGADO, CadastrarUsuarioInput(nome="X", login="xyz", senha="Senha@123", papel="AGENTE")
        )


async def test_alterar_papel_audita_antes_e_depois(gestao, auditoria):
    alvo = await _cadastrar(gestao)
    out = await AlterarPapelUsuario(*gestao).executar(SUPERVISOR, AlterarPapelInput(alvo.id, "perito"))
    assert out.papel == "PERITO"
    registro = auditoria.registros[-1]
    assert registro.dados_antes == {"papel": "AGENTE"} and registro.dados_depois == {"login": "ana.souza", "papel": "PERITO"}
    with pytest.raises(ValorInvalidoError):
        await AlterarPapelUsuario(*gestao).executar(SUPERVISOR, AlterarPapelInput(alvo.id, "PERITO"))


async def test_ninguem_age_sobre_a_propria_conta(gestao, usuarios):
    await usuarios.salvar(Usuario(id=SUPERVISOR.id, nome="Sup", login="supervisor", senha_hash="h", papel=Papel.SUPERVISOR))
    with pytest.raises(AcessoNegadoError):
        await AlterarPapelUsuario(*gestao).executar(SUPERVISOR, AlterarPapelInput(SUPERVISOR.id, "AGENTE"))
    with pytest.raises(AcessoNegadoError):
        await DesativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(SUPERVISOR.id))


async def test_desativar_e_reativar_sao_logicos(gestao, usuarios, auditoria):
    alvo = await _cadastrar(gestao)
    out = await DesativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(alvo.id, " Licença médica "))
    assert out.ativo is False and (await usuarios.buscar_por_id(alvo.id)) is not None
    assert auditoria.registros[-1].dados_depois == {"login": "ana.souza", "ativo": False, "motivo": "Licença médica"}
    with pytest.raises(ConflitoError):
        await DesativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(alvo.id))
    assert (await ReativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(alvo.id))).ativo is True
    with pytest.raises(ConflitoError):
        await ReativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(alvo.id))
    assert auditoria.operacoes()[-2:] == ["usuario.desativar", "usuario.reativar"]


async def test_usuario_de_sistema_e_inexistente_nao_sao_gerenciaveis(gestao, usuarios):
    cidadao = Usuario.sistema_cidadao()
    await usuarios.salvar(cidadao)
    for alvo in (cidadao.id, uuid4()):
        with pytest.raises(EntidadeNaoEncontradaError):
            await ReativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(alvo))
    assert [u.login for u in await ListarUsuariosGestao(usuarios).executar(SUPERVISOR)] == []
    with pytest.raises(AcessoNegadoError):
        await ListarUsuariosGestao(usuarios).executar(DELEGADO)


async def test_listagem_de_gestao_inclui_inativos(gestao, usuarios):
    alvo = await _cadastrar(gestao)
    await DesativarUsuario(*gestao).executar(SUPERVISOR, AlterarSituacaoUsuarioInput(alvo.id))
    [u] = await ListarUsuariosGestao(usuarios).executar(SUPERVISOR)
    assert u.id == alvo.id and u.ativo is False


def test_entidade_bloqueia_usuario_de_sistema():
    cidadao = Usuario.sistema_cidadao()
    with pytest.raises(ValorInvalidoError):
        cidadao.reativar()
    with pytest.raises(ValorInvalidoError):
        cidadao.alterar_papel(Papel.AGENTE)


async def test_operador_da_central_gerencia_como_o_supervisor(gestao, usuarios, auditoria):
    out = await CadastrarUsuario(*gestao, HasherFake()).executar(
        OPERADOR, CadastrarUsuarioInput(nome="Bia", login="bia", senha="Senha@123", papel="AGENTE")
    )
    assert (await AlterarPapelUsuario(*gestao).executar(OPERADOR, AlterarPapelInput(out.id, "PERITO"))).papel == "PERITO"
    assert (await DesativarUsuario(*gestao).executar(OPERADOR, AlterarSituacaoUsuarioInput(out.id))).ativo is False
    assert (await ReativarUsuario(*gestao).executar(OPERADOR, AlterarSituacaoUsuarioInput(out.id))).ativo is True
    assert [u.login for u in await ListarUsuariosGestao(usuarios).executar(OPERADOR)] == ["bia"]
    assert {r.quem for r in auditoria.registros} == {OPERADOR.id}
    with pytest.raises(AcessoNegadoError):
        await DesativarUsuario(*gestao).executar(OPERADOR, AlterarSituacaoUsuarioInput(OPERADOR.id))


@pytest.mark.parametrize("ator", [AGENTE, DELEGADO])
async def test_demais_papeis_nao_gerenciam(gestao, usuarios, ator):
    with pytest.raises(AcessoNegadoError):
        await ListarUsuariosGestao(usuarios).executar(ator)
    with pytest.raises(AcessoNegadoError):
        await AlterarPapelUsuario(*gestao).executar(ator, AlterarPapelInput(uuid4(), "AGENTE"))
