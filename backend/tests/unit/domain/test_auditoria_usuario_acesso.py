"""Eventos de auditoria de usuários, autenticação, acesso e exportação (payloads iguais aos anteriores)."""
from datetime import UTC, datetime
from uuid import uuid4

from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.exportacao import ExportacaoAuditoria, ExportacaoOcorrencias, exportacao_de
from domain.usuario.auditoria import (
    AcessoNegado,
    LoginBloqueado,
    LoginNegado,
    LoginRealizado,
    PapelUsuarioAlterado,
    UsuarioCadastrado,
    UsuarioDesativado,
    UsuarioReativado,
)
from domain.usuario.entity import Papel, Usuario

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
CONTEXTO = ContextoAuditoria(quem=uuid4(), quando=AGORA, ip="10.0.0.1")


def _usuario() -> Usuario:
    return Usuario.cadastrar(nome="Maria Souza", login="maria.souza", senha_hash="hash", papel=Papel.AGENTE)


def test_operacoes_e_entidades():
    assert {c.OPERACAO: c.ENTIDADE for c in (UsuarioCadastrado, PapelUsuarioAlterado, UsuarioDesativado, UsuarioReativado)} == {
        "usuario.cadastrar": "Usuario",
        "usuario.alterar_papel": "Usuario",
        "usuario.desativar": "Usuario",
        "usuario.reativar": "Usuario",
    }
    assert {c.OPERACAO: c.ENTIDADE for c in (LoginRealizado, LoginNegado, LoginBloqueado, AcessoNegado)} == {
        "auth.login": "Usuario",
        "auth.login_negado": "Usuario",
        "auth.login_bloqueado": "Usuario",
        "auth.acesso_negado": "Rota",
    }
    assert (ExportacaoOcorrencias.OPERACAO, ExportacaoAuditoria.OPERACAO) == ("ocorrencias.exportar", "auditoria.exportar")
    assert ExportacaoOcorrencias.ENTIDADE == ExportacaoAuditoria.ENTIDADE == "Exportacao"


def test_gestao_de_usuarios_sempre_leva_o_login():
    usuario = _usuario()

    cadastro = UsuarioCadastrado.de(usuario).para_registro(CONTEXTO)
    papel = PapelUsuarioAlterado.de(usuario, anterior=Papel.ESCRIVAO).para_registro(CONTEXTO)
    desativado = UsuarioDesativado.de(usuario, motivo="  Afastamento  ").para_registro(CONTEXTO)
    reativado = UsuarioReativado.de(usuario, motivo="").para_registro(CONTEXTO)

    assert cadastro.entidade_id == str(usuario.id) and cadastro.dados_antes is None
    assert cadastro.dados_depois == {"login": "maria.souza", "nome": "Maria Souza", "papel": "AGENTE", "ativo": True}
    assert papel.dados_antes == {"papel": "ESCRIVAO"} and papel.dados_depois == {"login": "maria.souza", "papel": "AGENTE"}
    assert desativado.dados_antes == {"ativo": True}
    assert desativado.dados_depois == {"login": "maria.souza", "ativo": False, "motivo": "Afastamento"}
    assert reativado.dados_antes == {"ativo": False}
    assert reativado.dados_depois == {"login": "maria.souza", "ativo": True, "motivo": None}


def test_login_realizado():
    usuario = _usuario()

    registro = LoginRealizado.de(usuario).para_registro(ContextoAuditoria(quem=usuario.id, quando=AGORA, ip="10.0.0.9"))

    assert (registro.quem, registro.entidade_id, registro.ip) == (usuario.id, str(usuario.id), "10.0.0.9")
    assert registro.dados_depois == {"papel": "AGENTE"}


def test_tentativas_recusadas_identificam_pelo_login_digitado():
    usuario = _usuario()
    anonimo = ContextoAuditoria(quem=None, quando=AGORA, ip="10.0.0.9")

    negado = LoginNegado(login="maria.souza", usuario_alvo_id=usuario.id, motivo="senha_invalida").para_registro(anonimo)
    inexistente = LoginNegado(login="ninguem", usuario_alvo_id=None, motivo="login_inexistente").para_registro(anonimo)
    bloqueado = LoginBloqueado(login="", usuario_alvo_id=None, bloqueado_ate=AGORA).para_registro(anonimo)

    assert negado.quem is None and negado.entidade_id == "maria.souza"
    assert negado.dados_depois == {"motivo": "senha_invalida", "usuario_alvo_id": str(usuario.id)}
    assert inexistente.dados_depois == {"motivo": "login_inexistente"}
    assert bloqueado.entidade_id is None and bloqueado.dados_depois == {"bloqueado_ate": AGORA.isoformat()}


def test_acesso_negado_a_rota():
    registro = AcessoNegado(rota="GET /v1/auditoria", papel=Papel.AGENTE, exigido=(Papel.DELEGADO, Papel.SUPERVISOR)).para_registro(CONTEXTO)

    assert registro.entidade_id == "GET /v1/auditoria"
    assert registro.dados_depois == {"papel": "AGENTE", "exigido": ["DELEGADO", "SUPERVISOR"]}


def test_exportacao_escolhe_a_classe_pelo_recurso():
    evento = exportacao_de("ocorrencias", formato="csv", filtros={"status": ["VALIDADA"]}, total_linhas=12)
    registro = evento.para_registro(CONTEXTO)

    assert isinstance(evento, ExportacaoOcorrencias)
    assert (registro.operacao, registro.entidade_id) == ("ocorrencias.exportar", "ocorrencias")
    assert registro.dados_depois == {"formato": "csv", "filtros": {"status": ["VALIDADA"]}, "total_linhas": 12}
    assert isinstance(exportacao_de("auditoria", formato="csv", filtros={}, total_linhas=0), ExportacaoAuditoria)
