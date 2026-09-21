"""Adapter de entrada: despacho tático e encerramento (RF02)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.http.v1.ocorrencias_router import OcorrenciaDetalheSchema, _detalhe
from adapters.inbound.http.v1.viaturas_router import ViaturaSchema, _schema as _viatura_schema
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_despachar_viatura import (
    DespacharInput,
    EncerrarInput,
    InterfaceDespacharViatura,
    InterfaceEncerrarOcorrencia,
    InterfaceListarOrdensDespacho,
    InterfaceSugerirViaturasProximas,
    ListarOrdensInput,
    OrdemDespachoOutput,
)
from domain.usuario.entity import Papel
from infrastructure.di import get_despachar_viatura, get_encerrar_ocorrencia, get_listar_ordens, get_sugerir_viaturas

router = APIRouter(tags=["despacho"])
DESPACHO = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)


class ViaturaSugeridaSchema(BaseModel):
    viatura: ViaturaSchema
    distancia_km: float


class SugestoesSchema(BaseModel):
    ocorrencia_id: UUID
    sugestoes: list[ViaturaSugeridaSchema]
    sem_elegiveis: bool
    disponiveis_sem_posicao: list[ViaturaSchema]


class DespacharRequest(BaseModel):
    ocorrencia_id: UUID
    viatura_id: UUID
    observacoes: str | None = Field(default=None, max_length=2000)


class OrdemDespachoSchema(BaseModel):
    id: UUID
    numero: str
    ocorrencia_id: UUID
    viatura_id: UUID
    operador_id: UUID
    criada_em: str
    observacoes: str | None
    ativa: bool
    encerrada_em: str | None


class EncerrarRequest(BaseModel):
    desfecho: str = Field(min_length=1, max_length=4000)


def _ordem(o: OrdemDespachoOutput) -> OrdemDespachoSchema:
    return OrdemDespachoSchema(**o.__dict__)


@router.get("/v1/ocorrencias/{ocorrencia_id}/sugestoes-viaturas", response_model=SugestoesSchema)
async def sugerir_viaturas(ocorrencia_id: UUID, ator: Ator = Depends(exigir_papel(*DESPACHO)), uc: InterfaceSugerirViaturasProximas = Depends(get_sugerir_viaturas)):
    """As N viaturas DISPONIVEL com posição válida mais próximas (Haversine) da ocorrência VALIDADA (RF02)."""
    out = await uc.executar(ator, ocorrencia_id)
    return SugestoesSchema(
        ocorrencia_id=out.ocorrencia_id,
        sugestoes=[ViaturaSugeridaSchema(viatura=_viatura_schema(s.viatura), distancia_km=s.distancia_km) for s in out.sugestoes],
        sem_elegiveis=out.sem_elegiveis,
        disponiveis_sem_posicao=[_viatura_schema(v) for v in out.disponiveis_sem_posicao],
    )


@router.post("/v1/despachos", response_model=OrdemDespachoSchema, status_code=201)
async def despachar(body: DespacharRequest, ator: Ator = Depends(exigir_papel(*DESPACHO)), uc: InterfaceDespacharViatura = Depends(get_despachar_viatura)):
    """Cria a ordem de despacho atomicamente: ocorrência → EM_ATENDIMENTO, viatura → EM_DESLOCAMENTO (RF02, RNF03)."""
    return _ordem(await uc.executar(ator, DespacharInput(ocorrencia_id=body.ocorrencia_id, viatura_id=body.viatura_id, observacoes=body.observacoes)))


@router.get("/v1/despachos", response_model=list[OrdemDespachoSchema])
async def listar_despachos(
    ocorrencia_id: UUID | None = Query(default=None),
    somente_ativas: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    ator: Ator = Depends(exigir_papel(Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR, Papel.DELEGADO)),
    uc: InterfaceListarOrdensDespacho = Depends(get_listar_ordens),
):
    return [_ordem(o) for o in await uc.executar(ator, ListarOrdensInput(ocorrencia_id=ocorrencia_id, somente_ativas=somente_ativas, limit=limit))]


@router.post("/v1/ocorrencias/{ocorrencia_id}/encerrar", response_model=OcorrenciaDetalheSchema)
async def encerrar(ocorrencia_id: UUID, body: EncerrarRequest, ator: Ator = Depends(exigir_papel(Papel.OPERADOR_CENTRAL, Papel.DELEGADO, Papel.SUPERVISOR)), uc: InterfaceEncerrarOcorrencia = Depends(get_encerrar_ocorrencia)):
    """EM_ATENDIMENTO → ENCERRADA; viaturas das ordens ativas voltam a DISPONIVEL (RF02)."""
    return _detalhe(await uc.executar(ator, EncerrarInput(ocorrencia_id=ocorrencia_id, desfecho=body.desfecho)))
