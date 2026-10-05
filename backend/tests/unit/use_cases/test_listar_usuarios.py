"""Testes unitários de ListarUsuarios (RF12) — sem banco."""
import pytest

from application.use_cases.usuario.listar_usuarios import ListarUsuarios
from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel, Usuario
from tests.fakes.atores import AGENTE, DELEGADO
from tests.fakes.auth_fake import RepositorioUsuarioFake


@pytest.fixture
def use_case():
    repo = RepositorioUsuarioFake()
    for nome, login, papel, ativo in [("Agente", "agente", Papel.AGENTE, True), ("Delegado", "delegado", Papel.DELEGADO, True), ("Inativo", "inativo", Papel.AGENTE, False)]:
        u = Usuario(nome=nome, login=login, senha_hash="hash::x", papel=papel, ativo=ativo)
        repo._store[u.id] = u
    return ListarUsuarios(repo)


async def test_lista_somente_ativos_sem_senha(use_case):
    saida = await use_case.executar(DELEGADO)
    assert sorted(u.login for u in saida) == ["agente", "delegado"]
    assert not any(hasattr(u, "senha_hash") for u in saida)


async def test_agente_pode_consultar_e_perito_nao(use_case):
    assert len(await use_case.executar(AGENTE)) == 2
    perito = type(AGENTE)(id=AGENTE.id, login="perito", papel=Papel.PERITO)
    with pytest.raises(AcessoNegadoError):
        await use_case.executar(perito)
