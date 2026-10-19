"""Testes unitários de AutenticarUsuario (RNF02) — sem banco."""
from datetime import UTC, datetime

import pytest

from application.ports.inbound.interface_autenticar_usuario import AutenticarInput
from application.use_cases.auth.autenticar_usuario import AutenticarUsuario
from domain.shared.exceptions import CredenciaisInvalidasError, MuitasTentativasError
from domain.usuario.entity import Papel, Usuario
from tests.fakes.auth_fake import HasherFake, LimitadorTentativasFake, ProvedorTokenFake, RepositorioUsuarioFake
from tests.fakes.portas_fake import AuditoriaFake, RelogioFake, UnidadeDeTrabalhoFake

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


@pytest.fixture
def repo():
    r = RepositorioUsuarioFake()
    h = HasherFake()
    r._store = {}
    for nome, login, papel, ativo in [
        ("Agente", "agente", Papel.AGENTE, True),
        ("Delegado", "Delegado", Papel.DELEGADO, True),
        ("Inativo", "inativo", Papel.AGENTE, False),
    ]:
        u = Usuario(nome=nome, login=login, senha_hash=h.gerar_hash("Senha@123"), papel=papel, ativo=ativo)
        r._store[u.id] = u
    return r


@pytest.fixture
def auditoria():
    return AuditoriaFake()


@pytest.fixture
def limitador():
    return LimitadorTentativasFake(maximo=3)


@pytest.fixture
def relogio():
    return RelogioFake(AGORA)


@pytest.fixture
def use_case(repo, auditoria, limitador, relogio):
    return AutenticarUsuario(repo, HasherFake(), ProvedorTokenFake(), relogio, auditoria, UnidadeDeTrabalhoFake(), limitador)


async def test_login_valido_emite_token_de_8h(use_case, auditoria):
    out = await use_case.executar(AutenticarInput(login="agente", senha="Senha@123", ip="10.0.0.1"))
    assert out.token_type == "bearer"
    assert out.usuario.papel == "AGENTE"
    assert out.expira_em == "2026-09-13T20:00:00+00:00"
    assert auditoria.operacoes() == ["auth.login"] and auditoria.registros[0].ip == "10.0.0.1"


async def test_login_e_case_insensitive(use_case):
    out = await use_case.executar(AutenticarInput(login="DELEGADO", senha="Senha@123"))
    assert out.usuario.login == "delegado"


@pytest.mark.parametrize(
    "login,senha,motivo",
    [("agente", "errada", "senha_invalida"), ("naoexiste", "Senha@123", "login_inexistente"), ("inativo", "Senha@123", "usuario_inativo"), ("", "", "login_inexistente")],
)
async def test_falhas_devolvem_401_generico_e_auditam(use_case, auditoria, login, senha, motivo):
    with pytest.raises(CredenciaisInvalidasError) as exc:
        await use_case.executar(AutenticarInput(login=login, senha=senha))
    assert exc.value.chave == "auth.credenciais_invalidas"
    assert auditoria.operacoes() == ["auth.login_negado"]
    registro = auditoria.registros[0]
    assert registro.quem is None  # quem tentou é desconhecido — nunca o usuário-alvo
    assert registro.dados_depois["motivo"] == motivo
    assert ("usuario_alvo_id" in registro.dados_depois) == (motivo != "login_inexistente")


async def test_token_decodifica_e_expira(repo):
    prov, relogio = ProvedorTokenFake(), RelogioFake(AGORA)
    uc = AutenticarUsuario(repo, HasherFake(), prov, relogio, AuditoriaFake(), UnidadeDeTrabalhoFake(), LimitadorTentativasFake())
    out = await uc.executar(AutenticarInput(login="agente", senha="Senha@123"))
    dados = prov.decodificar(out.access_token, AGORA)
    assert dados.papel == Papel.AGENTE
    relogio.avancar(hours=9)
    with pytest.raises(CredenciaisInvalidasError):
        prov.decodificar(out.access_token, relogio.agora())


async def test_forca_bruta_bloqueia_login_ip_mesmo_com_senha_correta(use_case, auditoria, relogio):
    for _ in range(3):
        with pytest.raises(CredenciaisInvalidasError):
            await use_case.executar(AutenticarInput(login="agente", senha="errada", ip="10.0.0.9"))
    with pytest.raises(MuitasTentativasError) as exc:
        await use_case.executar(AutenticarInput(login="agente", senha="Senha@123", ip="10.0.0.9"))
    assert exc.value.chave == "auth.muitas_tentativas"
    assert exc.value.detalhes["retry_after_segundos"] == 15 * 60
    assert auditoria.operacoes()[-1] == "auth.login_bloqueado" and auditoria.registros[-1].quem is None


async def test_bloqueio_e_por_ip_e_expira(use_case, relogio):
    for _ in range(3):
        with pytest.raises(CredenciaisInvalidasError):
            await use_case.executar(AutenticarInput(login="agente", senha="errada", ip="10.0.0.9"))
    out = await use_case.executar(AutenticarInput(login="agente", senha="Senha@123", ip="10.0.0.1"))
    assert out.usuario.login == "agente"  # outro IP não é afetado (evita negar serviço ao titular)
    relogio.avancar(minutes=16)
    out = await use_case.executar(AutenticarInput(login="agente", senha="Senha@123", ip="10.0.0.9"))
    assert out.usuario.login == "agente"


async def test_login_valido_zera_contagem_de_falhas(use_case, limitador):
    for _ in range(2):
        with pytest.raises(CredenciaisInvalidasError):
            await use_case.executar(AutenticarInput(login="agente", senha="errada", ip="10.0.0.9"))
    await use_case.executar(AutenticarInput(login="agente", senha="Senha@123", ip="10.0.0.9"))
    assert limitador.contagem == {}
