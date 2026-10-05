"""
Casos de uso de gestão do efetivo (sugestão #13 — RNF02): ListarUsuariosGestao, CadastrarUsuario,
AlterarPapelUsuario, DesativarUsuario e ReativarUsuario.

Regras: só o SUPERVISOR executa; ninguém altera o próprio papel nem a própria situação; nada é
apagado (``ativo = false``); tudo é auditado com o estado anterior e o novo. A sessão de quem foi
desativado ou mudou de papel deixa de valer na requisição seguinte (o token é conferido contra o
cadastro a cada chamada).
"""
from __future__ import annotations

from typing import Any

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_usuarios import (
    AlterarPapelInput,
    AlterarSituacaoUsuarioInput,
    CadastrarUsuarioInput,
    InterfaceAlterarPapelUsuario,
    InterfaceCadastrarUsuario,
    InterfaceDesativarUsuario,
    InterfaceListarUsuariosGestao,
    InterfaceReativarUsuario,
    UsuarioGestaoOutput,
)
from application.ports.outbound.hasher_senha import HasherSenha
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError, ValorInvalidoError
from domain.usuario.entity import TAMANHO_MINIMO_SENHA, Papel, Usuario, interpretar_papel

PAPEL_GESTOR = Papel.SUPERVISOR
ENTIDADE_USUARIO = "Usuario"


def para_gestao(u: Usuario) -> UsuarioGestaoOutput:
    return UsuarioGestaoOutput(id=u.id, nome=u.nome, login=u.login, papel=u.papel.value, ativo=u.ativo)


class ListarUsuariosGestao(InterfaceListarUsuariosGestao):
    def __init__(self, repositorio: RepositorioUsuario) -> None:
        self._repositorio = repositorio

    async def executar(self, ator: Ator) -> tuple[UsuarioGestaoOutput, ...]:
        ator.exigir_papel(PAPEL_GESTOR)
        return tuple(para_gestao(u) for u in await self._repositorio.listar() if u.papel != Papel.CIDADAO)


class _GestaoBase:
    def __init__(
        self, repositorio: RepositorioUsuario, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria

    async def _registrar(
        self, ator: Ator, operacao: str, usuario: Usuario, antes: dict[str, Any] | None, depois: dict[str, Any]
    ) -> None:
        await self._auditoria.registrar(
            RegistroAuditoria(
                quem=ator.id,
                quando=self._relogio.agora(),
                operacao=operacao,
                entidade=ENTIDADE_USUARIO,
                entidade_id=str(usuario.id),
                dados_antes=antes,
                dados_depois={"login": usuario.login, **depois},
                ip=ator.ip,
            )
        )

    async def _alvo(self, ator: Ator, usuario_id) -> Usuario:
        """Carrega o usuário-alvo; o Supervisor não age sobre a própria conta."""
        ator.exigir_papel(PAPEL_GESTOR)
        if usuario_id == ator.id:
            raise AcessoNegadoError("Ninguém altera o próprio papel ou situação.", chave="usuario.proprio")
        usuario = await self._repositorio.buscar_por_id(usuario_id)
        if usuario is None or usuario.papel == Papel.CIDADAO:
            raise EntidadeNaoEncontradaError("Usuário não encontrado.", chave="usuario.nao_encontrado")
        return usuario


class CadastrarUsuario(_GestaoBase, InterfaceCadastrarUsuario):
    def __init__(
        self,
        repositorio: RepositorioUsuario,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        hasher: HasherSenha,
    ) -> None:
        super().__init__(repositorio, uow, relogio, auditoria)
        self._hasher = hasher

    async def executar(self, ator: Ator, input_dto: CadastrarUsuarioInput) -> UsuarioGestaoOutput:
        ator.exigir_papel(PAPEL_GESTOR)
        papel = interpretar_papel(input_dto.papel)
        if len(input_dto.senha or "") < TAMANHO_MINIMO_SENHA:
            raise ValorInvalidoError(
                f"A senha inicial deve ter ao menos {TAMANHO_MINIMO_SENHA} caracteres.",
                chave="usuario.senha_curta",
                minimo=TAMANHO_MINIMO_SENHA,
            )
        usuario = Usuario.cadastrar(
            nome=input_dto.nome, login=input_dto.login, senha_hash=self._hasher.gerar_hash(input_dto.senha), papel=papel
        )
        async with self._uow:
            if await self._repositorio.buscar_por_login(usuario.login) is not None:
                raise ConflitoError("Login já está em uso.", chave="usuario.login_em_uso")
            await self._repositorio.salvar(usuario)
            await self._registrar(ator, "usuario.cadastrar", usuario, None, {"nome": usuario.nome, "papel": papel.value, "ativo": True})
            await self._uow.commit()
        return para_gestao(usuario)


class AlterarPapelUsuario(_GestaoBase, InterfaceAlterarPapelUsuario):
    async def executar(self, ator: Ator, input_dto: AlterarPapelInput) -> UsuarioGestaoOutput:
        novo = interpretar_papel(input_dto.papel)
        async with self._uow:
            usuario = await self._alvo(ator, input_dto.usuario_id)
            anterior = usuario.alterar_papel(novo)
            await self._repositorio.salvar(usuario)
            await self._registrar(ator, "usuario.alterar_papel", usuario, {"papel": anterior.value}, {"papel": novo.value})
            await self._uow.commit()
        return para_gestao(usuario)


class DesativarUsuario(_GestaoBase, InterfaceDesativarUsuario):
    async def executar(self, ator: Ator, input_dto: AlterarSituacaoUsuarioInput) -> UsuarioGestaoOutput:
        async with self._uow:
            usuario = await self._alvo(ator, input_dto.usuario_id)
            usuario.desativar()
            await self._repositorio.salvar(usuario)
            await self._registrar(
                ator, "usuario.desativar", usuario, {"ativo": True}, {"ativo": False, "motivo": (input_dto.motivo or "").strip() or None}
            )
            await self._uow.commit()
        return para_gestao(usuario)


class ReativarUsuario(_GestaoBase, InterfaceReativarUsuario):
    async def executar(self, ator: Ator, input_dto: AlterarSituacaoUsuarioInput) -> UsuarioGestaoOutput:
        async with self._uow:
            usuario = await self._alvo(ator, input_dto.usuario_id)
            usuario.reativar()
            await self._repositorio.salvar(usuario)
            await self._registrar(
                ator, "usuario.reativar", usuario, {"ativo": False}, {"ativo": True, "motivo": (input_dto.motivo or "").strip() or None}
            )
            await self._uow.commit()
        return para_gestao(usuario)
