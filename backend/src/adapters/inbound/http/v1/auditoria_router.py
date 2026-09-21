"""Adapter de entrada: /v1/auditoria (RF20) — leitura, somente Delegado/Supervisor."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_auditoria import ConsultarAuditoriaInput, InterfaceConsultarAuditoria
from domain.usuario.entity import Papel
from infrastructure.di import get_consultar_auditoria

router = APIRouter(prefix="/v1/auditoria", tags=["auditoria"])


class RegistroAuditoriaSchema(BaseModel):
    id: UUID
    quem: UUID | None
    quando: str
    operacao: str
    entidade: str
    entidade_id: str | None
    dados_antes: dict[str, Any] | None
    dados_depois: dict[str, Any] | None
    ip: str | None


@router.get("", response_model=list[RegistroAuditoriaSchema])
async def listar_auditoria(
    entidade: str | None = Query(default=None),
    entidade_id: str | None = Query(default=None),
    operacao: str | None = Query(default=None),
    quem: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR)),
    use_case: InterfaceConsultarAuditoria = Depends(get_consultar_auditoria),
) -> list[RegistroAuditoriaSchema]:
    """Trilha de auditoria append-only (mais recente primeiro)."""
    registros = await use_case.executar(
        ator,
        ConsultarAuditoriaInput(
            entidade=entidade,
            entidade_id=entidade_id,
            operacao=operacao,
            quem=quem,
            limit=limit,
        ),
    )
    return [RegistroAuditoriaSchema(**r.__dict__) for r in registros]
