"""Adapter de entrada: /v1/viaturas, /v1/telemetria e /v1/simulador (RF02)."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.simulador.simulador_telemetria import SimuladorTelemetria
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_viaturas import (
    AlterarSituacaoInput,
    CadastrarViaturaInput,
    InterfaceAlterarSituacaoViatura,
    InterfaceCadastrarViatura,
    InterfaceListarViaturas,
    InterfaceRegistrarPosicaoViatura,
    RegistrarPosicaoInput,
    ViaturaOutput,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_alterar_situacao_viatura,
    get_cadastrar_viatura,
    get_listar_viaturas,
    get_registrar_posicao_viatura,
    get_simulador,
)

router = APIRouter(tags=["viaturas"])
GESTAO = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
CONSULTA = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR, Papel.DELEGADO, Papel.AGENTE)


class ViaturaSchema(BaseModel):
    id: UUID
    prefixo: str
    placa: str
    situacao: str
    latitude: float | None
    longitude: float | None
    posicao_registrada_em: str | None
    sinal: str
    versao: int


class CadastrarViaturaRequest(BaseModel):
    prefixo: str = Field(min_length=1, max_length=20)
    placa: str = Field(min_length=1, max_length=10)


class AlterarSituacaoRequest(BaseModel):
    situacao: str  # DISPONIVEL | INDISPONIVEL


class PosicaoRequest(BaseModel):
    viatura_id: UUID
    latitude: float
    longitude: float
    registrada_em: datetime


def _schema(v: ViaturaOutput) -> ViaturaSchema:
    return ViaturaSchema(**v.__dict__)


@router.get("/v1/viaturas", response_model=list[ViaturaSchema])
async def listar_viaturas(ator: Ator = Depends(exigir_papel(*CONSULTA)), uc: InterfaceListarViaturas = Depends(get_listar_viaturas)):
    """Frota com última posição e indicador de sinal (RF02, RNF04*)."""
    return [_schema(v) for v in await uc.executar(ator)]


@router.post("/v1/viaturas", response_model=ViaturaSchema, status_code=201)
async def cadastrar_viatura(body: CadastrarViaturaRequest, ator: Ator = Depends(exigir_papel(*GESTAO)), uc: InterfaceCadastrarViatura = Depends(get_cadastrar_viatura)):
    """Cadastra viatura; prefixo/placa duplicados → 409 (RF02)."""
    return _schema(await uc.executar(ator, CadastrarViaturaInput(prefixo=body.prefixo, placa=body.placa)))


@router.patch("/v1/viaturas/{viatura_id}/situacao", response_model=ViaturaSchema)
async def alterar_situacao(viatura_id: UUID, body: AlterarSituacaoRequest, ator: Ator = Depends(exigir_papel(*GESTAO)), uc: InterfaceAlterarSituacaoViatura = Depends(get_alterar_situacao_viatura)):
    """DISPONIVEL ⇄ INDISPONIVEL manual (RF02)."""
    return _schema(await uc.executar(ator, AlterarSituacaoInput(viatura_id=viatura_id, situacao=body.situacao)))


@router.post("/v1/telemetria/posicoes", response_model=ViaturaSchema, tags=["telemetria"])
async def registrar_posicao(body: PosicaoRequest, ator: Ator = Depends(exigir_papel(*GESTAO)), uc: InterfaceRegistrarPosicaoViatura = Depends(get_registrar_posicao_viatura)):
    """Ingestão de posição GPS (RF02). Timestamp fora de ±60 s → 422; posição anterior é mantida."""
    return _schema(await uc.executar(RegistrarPosicaoInput(viatura_id=body.viatura_id, latitude=body.latitude, longitude=body.longitude, registrada_em=body.registrada_em, origem=f"http:{ator.login}")))


@router.get("/v1/simulador", tags=["telemetria"])
async def status_simulador(ator: Ator = Depends(exigir_papel(*CONSULTA)), sim: SimuladorTelemetria = Depends(get_simulador)) -> dict:
    return sim.status()


@router.post("/v1/simulador/ligar", tags=["telemetria"])
async def ligar_simulador(ator: Ator = Depends(exigir_papel(*GESTAO)), sim: SimuladorTelemetria = Depends(get_simulador)) -> dict:
    """Liga o simulador de telemetria a 1 Hz (RF02)."""
    sim.ligar()
    return sim.status()


@router.post("/v1/simulador/desligar", tags=["telemetria"])
async def desligar_simulador(ator: Ator = Depends(exigir_papel(*GESTAO)), sim: SimuladorTelemetria = Depends(get_simulador)) -> dict:
    await sim.desligar()
    return sim.status()
