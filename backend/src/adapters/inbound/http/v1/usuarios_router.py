"""Adapter de entrada: /v1/usuarios (RF12) — efetivo ativo para a tela inicial."""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_listar_usuarios import InterfaceListarUsuarios
from domain.usuario.entity import Papel
from infrastructure.di import get_listar_usuarios

router = APIRouter(prefix="/v1/usuarios", tags=["usuarios"])
CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)


class UsuarioResumoSchema(BaseModel):
    id: UUID
    nome: str
    login: str
    papel: str


@router.get("", response_model=list[UsuarioResumoSchema])
async def listar_usuarios(
    ator: Ator = Depends(exigir_papel(*CONSULTA)),
    uc: InterfaceListarUsuarios = Depends(get_listar_usuarios),
) -> list[UsuarioResumoSchema]:
    """Efetivo ativo (nome, login e papel); sem credenciais (RF12)."""
    return [UsuarioResumoSchema(**u.__dict__) for u in await uc.executar(ator)]
