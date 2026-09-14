"""Adapter de entrada: /v1/auth (RF11)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import ator_atual, ip_do_cliente
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_autenticar_usuario import AutenticarInput, InterfaceAutenticarUsuario
from infrastructure.di import get_autenticar_usuario

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=100)
    senha: str = Field(min_length=1, max_length=200)


class UsuarioSchema(BaseModel):
    id: UUID
    nome: str
    login: str
    papel: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expira_em: str
    usuario: UsuarioSchema


class AtorSchema(BaseModel):
    id: UUID
    login: str
    papel: str


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    use_case: InterfaceAutenticarUsuario = Depends(get_autenticar_usuario),
) -> LoginResponse:
    """Autentica por login/senha e emite JWT de 8 h (RF11)."""
    out = await use_case.executar(AutenticarInput(login=body.login, senha=body.senha, ip=ip_do_cliente(request)))
    return LoginResponse(
        access_token=out.access_token,
        token_type=out.token_type,
        expira_em=out.expira_em,
        usuario=UsuarioSchema(id=out.usuario.id, nome=out.usuario.nome, login=out.usuario.login, papel=out.usuario.papel),
    )


@router.get("/me", response_model=AtorSchema)
async def me(ator: Ator = Depends(ator_atual)) -> AtorSchema:
    """Devolve o ator do token corrente."""
    return AtorSchema(id=ator.id, login=ator.login, papel=ator.papel.value)
