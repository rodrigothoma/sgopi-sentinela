"""
Caso de uso: AutenticarUsuario (RNF02).

Login + senha → token. Falhas (login inexistente, senha errada, usuário inativo)
devolvem a MESMA exceção para não vazar existência de login, e são auditadas sem
autor (``quem`` vazio): quem tentou é desconhecido; o usuário-alvo vai em ``dados_depois``.

Proteção contra força bruta: falhas são contadas por ``login|ip``; ao exceder o limite
o par fica bloqueado (HTTP 429) mesmo com a senha correta, e o bloqueio é auditado.
"""
from datetime import datetime

from application.ports.inbound.interface_autenticar_usuario import (
    AutenticarInput,
    AutenticarOutput,
    InterfaceAutenticarUsuario,
    UsuarioOutput,
)
from application.ports.outbound.hasher_senha import HasherSenha
from application.ports.outbound.limitador_tentativas import LimitadorTentativas
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.provedor_token import ProvedorToken
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import CredenciaisInvalidasError, MuitasTentativasError
from domain.usuario.entity import Usuario


class AutenticarUsuario(InterfaceAutenticarUsuario):
    def __init__(
        self,
        repositorio: RepositorioUsuario,
        hasher: HasherSenha,
        provedor_token: ProvedorToken,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        uow: UnidadeDeTrabalho,
        limitador: LimitadorTentativas,
    ) -> None:
        self._repositorio = repositorio
        self._hasher = hasher
        self._provedor_token = provedor_token
        self._relogio = relogio
        self._auditoria = auditoria
        self._uow = uow
        self._limitador = limitador

    async def executar(self, input_dto: AutenticarInput) -> AutenticarOutput:
        agora = self._relogio.agora()
        login = (input_dto.login or "").strip().lower()
        chave_limite = f"{login}|{input_dto.ip or '-'}"
        bloqueio = self._limitador.bloqueado_ate(chave_limite, agora)
        if bloqueio is not None:
            await self._auditar_falha("auth.login_bloqueado", login, None, {"bloqueado_ate": bloqueio.isoformat()}, input_dto.ip, agora)
            segundos = max(1, int((bloqueio - agora).total_seconds()))
            raise MuitasTentativasError(
                "Muitas tentativas de login.", chave="auth.muitas_tentativas", retry_after_segundos=segundos
            )

        usuario = await self._repositorio.buscar_por_login(login) if login else None
        motivo = self._motivo_falha(usuario, input_dto.senha or "")
        if motivo:
            self._limitador.registrar(chave_limite, agora)
            await self._auditar_falha("auth.login_negado", login, usuario, {"motivo": motivo}, input_dto.ip, agora)
            raise CredenciaisInvalidasError("Credenciais inválidas.", chave="auth.credenciais_invalidas")
        self._limitador.limpar(chave_limite)

        assert usuario is not None
        token, expira_em = self._provedor_token.emitir(usuario.id, usuario.login, usuario.papel, agora)
        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=usuario.id,
                    quando=agora,
                    operacao="auth.login",
                    entidade="Usuario",
                    entidade_id=str(usuario.id),
                    dados_depois={"papel": usuario.papel.value},
                    ip=input_dto.ip,
                )
            )
            await self._uow.commit()

        return AutenticarOutput(
            access_token=token,
            token_type="bearer",
            expira_em=expira_em.isoformat(),
            usuario=UsuarioOutput(id=usuario.id, nome=usuario.nome, login=usuario.login, papel=usuario.papel.value),
        )

    def _motivo_falha(self, usuario: Usuario | None, senha: str) -> str | None:
        if usuario is None:
            return "login_inexistente"
        if not usuario.ativo:
            return "usuario_inativo"
        if not self._hasher.verificar(senha, usuario.senha_hash):
            return "senha_invalida"
        return None

    async def _auditar_falha(
        self, operacao: str, login: str, usuario: Usuario | None, dados: dict, ip: str | None, agora: datetime
    ) -> None:
        if usuario is not None:
            dados = {**dados, "usuario_alvo_id": str(usuario.id)}
        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=None,
                    quando=agora,
                    operacao=operacao,
                    entidade="Usuario",
                    entidade_id=login or None,
                    dados_depois=dados,
                    ip=ip,
                )
            )
            await self._uow.commit()
