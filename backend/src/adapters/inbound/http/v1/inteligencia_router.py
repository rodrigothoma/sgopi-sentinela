"""
Adapter de entrada HTTP: /v1/inteligencia (RF05 / UC05 / UC11 / UC14).

Inteligência de Segurança Pública: Manchas Criminais / Áreas de Risco e Alertas de Criticidade Tática.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import ator_atual, exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_inteligencia_areas_risco import (
    InterfaceCalcularAreasRisco,
    InterfaceConfirmarCienciaAlerta,
    InterfaceEmitirAlertaCriticidade,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_calcular_areas_risco,
    get_confirmar_ciencia_alerta,
    get_emitir_alerta_criticidade,
)

router = APIRouter(prefix="/v1/inteligencia", tags=["inteligencia"])

PAPEIS_EMISSAO_ALERTA = (Papel.SUPERVISOR, Papel.DELEGADO, Papel.OPERADOR_CENTRAL)
PAPEIS_CIENCIA_ALERTA = (Papel.SUPERVISOR, Papel.DELEGADO)


class AreaRiscoSchema(BaseModel):
    id: str
    nome: str
    latitude: float
    longitude: float
    raio_metros: float
    nivel_risco: str
    total_ocorrencias: int
    total_24h: int
    naturezas_predominantes: list[str]
    protocolos: list[str]


class AlertaCriticidadeRequest(BaseModel):
    titulo: str = Field(min_length=5, max_length=200)
    mensagem: str = Field(min_length=10, max_length=1000)
    area_risco_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    raio_metros: float | None = None
    nivel_criticidade: str = "CRITICA"
    papel_destinatario: str | None = None


class AlertaCriticidadeResponse(BaseModel):
    alerta_id: str
    titulo: str
    status: str
    criada_em: str


class ConfirmarCienciaResponse(BaseModel):
    sucesso: bool
    alerta_id: str
    status: str


@router.get("/areas-risco", response_model=list[AreaRiscoSchema])
async def obter_areas_risco(
    dias: int = Query(7, ge=1, le=90),
    ator: Ator = Depends(ator_atual),
    uc: InterfaceCalcularAreasRisco = Depends(get_calcular_areas_risco),
) -> list[AreaRiscoSchema]:
    """Calcula dinamicamente áreas de risco / hotspots criminais com base nas ocorrências recentes."""
    areas = await uc.executar(dias=dias)
    return [AreaRiscoSchema(**a) for a in areas]


@router.post(
    "/alertas-criticidade/emitir",
    response_model=AlertaCriticidadeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def emitir_alerta_criticidade(
    req: AlertaCriticidadeRequest,
    ator: Ator = Depends(exigir_papel(*PAPEIS_EMISSAO_ALERTA)),
    uc: InterfaceEmitirAlertaCriticidade = Depends(get_emitir_alerta_criticidade),
) -> AlertaCriticidadeResponse:
    """Emite um alerta de criticidade operacional com difusão em tempo real e auditoria."""
    resultado = await uc.executar(ator=ator, dados_alerta=req.model_dump())
    return AlertaCriticidadeResponse(**resultado)


@router.post(
    "/alertas-criticidade/{alerta_id}/confirmar-ciencia",
    response_model=ConfirmarCienciaResponse,
)
async def confirmar_ciencia_alerta(
    alerta_id: str,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CIENCIA_ALERTA)),
    uc: InterfaceConfirmarCienciaAlerta = Depends(get_confirmar_ciencia_alerta),
) -> ConfirmarCienciaResponse:
    """Registra ciência formal de supervisão sobre alerta de criticidade emitido."""
    await uc.executar(ator=ator, alerta_id=alerta_id)
    return ConfirmarCienciaResponse(sucesso=True, alerta_id=alerta_id, status="CIENTE")
