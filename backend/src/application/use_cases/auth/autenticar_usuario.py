"""
Caso de uso: AutenticarUsuario (RF11 / RF12).

Login + senha → token. Falhas (login inexistente, senha errada, usuário inativo)
devolvem a MESMA exceção para não vazar existência de login, e são auditadas.
"""
from application.ports.inbound.interface_autenticar_usuario import (
    AutenticarInput,
    AutenticarOutput,
    InterfaceAutenticarUsuario,
    UsuarioOutput,
)
from application.ports.outbound.hasher_senha import HasherSenha
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.provedor_token import ProvedorToken
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import CredenciaisInvalidasError


class AutenticarUsuario(InterfaceAutenticarUsuario):
    def __init__(
        self,
        repositorio: RepositorioUsuario,
        hasher: HasherSenha,
        provedor_token: ProvedorToken,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        uow: UnidadeDeTrabalho,
    ) -> None:
        self._repositorio = repositorio
        self._hasher = hasher
        self._provedor_token = provedor_token
        self._relogio = relogio
        self._auditoria = auditoria
        self._uow = uow

    async def executar(self, input_dto: AutenticarInput) -> AutenticarOutput:
        agora = self._relogio.agora()
        login = (input_dto.login or "").strip().lower()
        usuario = await self._repositorio.buscar_por_login(login) if login else None

        motivo: str | None = None
        if usuario is None:
            motivo = "login_inexistente"
        elif not usuario.ativo:
            motivo = "usuario_inativo"
        elif not self._hasher.verificar(input_dto.senha or "", usuario.senha_hash):
            motivo = "senha_invalida"

        if motivo:
            async with self._uow:
                await self._auditoria.registrar(
                    RegistroAuditoria(
                        quem=usuario.id if usuario else None,
                        quando=agora,
                        operacao="auth.login_negado",
                        entidade="Usuario",
                        entidade_id=login or None,
                        dados_depois={"motivo": motivo},
                        ip=input_dto.ip,
                    )
                )
                await self._uow.commit()
            raise CredenciaisInvalidasError("Credenciais inválidas.", chave="auth.credenciais_invalidas")

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
