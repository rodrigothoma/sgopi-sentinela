"""Adapter de entrada: /v1/usuarios — efetivo ativo (RF12) e gestão pelo Supervisor e pelo Operador da Central (sugestão #13)."""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
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
from application.ports.inbound.interface_listar_usuarios import InterfaceListarUsuarios
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_alterar_papel_usuario,
    get_cadastrar_usuario,
    get_desativar_usuario,
    get_listar_usuarios,
    get_listar_usuarios_gestao,
    get_reativar_usuario,
)

router = APIRouter(prefix="/v1/usuarios", tags=["usuarios"])
CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
# Gestão do efetivo: Supervisor e Operador da Central (o caso de uso re-verifica)
GESTORES = (Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL)


class UsuarioResumoSchema(BaseModel):
    id: UUID
    nome: str
    login: str
    papel: str


class UsuarioGestaoSchema(UsuarioResumoSchema):
    ativo: bool


class CadastrarUsuarioRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    login: str = Field(min_length=1, max_length=50)
    senha: str = Field(min_length=1, max_length=128)
    papel: str = Field(max_length=30)


class AlterarPapelRequest(BaseModel):
    papel: str = Field(max_length=30)


class SituacaoRequest(BaseModel):
    motivo: str | None = Field(default=None, max_length=2000)


def _gestao(u: UsuarioGestaoOutput) -> UsuarioGestaoSchema:
    return UsuarioGestaoSchema(**u.__dict__)


@router.get("", response_model=list[UsuarioResumoSchema])
async def listar_usuarios(
    ator: Ator = Depends(exigir_papel(*CONSULTA)),
    uc: InterfaceListarUsuarios = Depends(get_listar_usuarios),
) -> list[UsuarioResumoSchema]:
    """Efetivo ativo (nome, login e papel); sem credenciais (RF12)."""
    return [UsuarioResumoSchema(**u.__dict__) for u in await uc.executar(ator)]


@router.get("/gestao", response_model=list[UsuarioGestaoSchema])
async def listar_usuarios_gestao(
    ator: Ator = Depends(exigir_papel(*GESTORES)),
    uc: InterfaceListarUsuariosGestao = Depends(get_listar_usuarios_gestao),
) -> list[UsuarioGestaoSchema]:
    """Todos os usuários, inclusive inativos (sem o usuário de sistema do canal público). Somente SUPERVISOR e OPERADOR_CENTRAL."""
    return [_gestao(u) for u in await uc.executar(ator)]


@router.post("", response_model=UsuarioGestaoSchema, status_code=201)
async def cadastrar_usuario(
    body: CadastrarUsuarioRequest,
    ator: Ator = Depends(exigir_papel(*GESTORES)),
    uc: InterfaceCadastrarUsuario = Depends(get_cadastrar_usuario),
) -> UsuarioGestaoSchema:
    """Cadastra um usuário ativo com senha inicial informada pelo gestor (auditado)."""
    return _gestao(await uc.executar(ator, CadastrarUsuarioInput(nome=body.nome, login=body.login, senha=body.senha, papel=body.papel)))


@router.patch("/{usuario_id}/papel", response_model=UsuarioGestaoSchema)
async def alterar_papel(
    usuario_id: UUID,
    body: AlterarPapelRequest,
    ator: Ator = Depends(exigir_papel(*GESTORES)),
    uc: InterfaceAlterarPapelUsuario = Depends(get_alterar_papel_usuario),
) -> UsuarioGestaoSchema:
    """Troca o papel (nunca o próprio); a sessão do usuário afetado deixa de valer."""
    return _gestao(await uc.executar(ator, AlterarPapelInput(usuario_id=usuario_id, papel=body.papel)))


@router.post("/{usuario_id}/desativar", response_model=UsuarioGestaoSchema)
async def desativar_usuario(
    usuario_id: UUID,
    body: SituacaoRequest | None = None,
    ator: Ator = Depends(exigir_papel(*GESTORES)),
    uc: InterfaceDesativarUsuario = Depends(get_desativar_usuario),
) -> UsuarioGestaoSchema:
    """Desativação lógica (``ativo = false``, nunca DELETE); a sessão aberta cai na próxima requisição."""
    motivo = body.motivo if body else None
    return _gestao(await uc.executar(ator, AlterarSituacaoUsuarioInput(usuario_id=usuario_id, motivo=motivo)))


@router.post("/{usuario_id}/reativar", response_model=UsuarioGestaoSchema)
async def reativar_usuario(
    usuario_id: UUID,
    body: SituacaoRequest | None = None,
    ator: Ator = Depends(exigir_papel(*GESTORES)),
    uc: InterfaceReativarUsuario = Depends(get_reativar_usuario),
) -> UsuarioGestaoSchema:
    """Devolve o usuário ao efetivo ativo."""
    motivo = body.motivo if body else None
    return _gestao(await uc.executar(ator, AlterarSituacaoUsuarioInput(usuario_id=usuario_id, motivo=motivo)))
