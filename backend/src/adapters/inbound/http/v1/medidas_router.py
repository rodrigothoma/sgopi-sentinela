"""
Adapter de entrada: /v1/medidas-protetivas — Gestão de Medidas Protetivas de Urgência (RF09 / UC09 / sq09).
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_alertas_vencimento_medida import (
    InterfaceEmitirAlertaVencimentoMedida,
)
from application.ports.inbound.interface_gerir_medidas_protetivas import (
    ConcederMedidaInput,
    InterfaceConcederMedida,
    InterfaceListarMedidas,
    InterfaceRenovarMedida,
    InterfaceRevogarMedida,
    MedidaProtetivaOutput,
    RenovarMedidaInput,
    RevogarMedidaInput,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_conceder_medida,
    get_emitir_alerta_vencimento,
    get_listar_medidas,
    get_renovar_medida,
    get_revogar_medida,
)

router = APIRouter(prefix="/v1/medidas-protetivas", tags=["medidas-protetivas"])

PAPEIS_CONSULTA = (Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL, Papel.AGENTE, Papel.ESCRIVAO)


# ------------------------------------------------------------------ schemas
class ConcederMedidaRequest(BaseModel):
    ocorrencia_id: UUID
    vitima_id: UUID
    agressor_id: UUID
    tipos_restricao: list[str] = Field(min_length=1)
    prazo_dias: int = Field(ge=1, le=730)
    data_inicio: date | None = None
    distancia_minima_metros: int | None = Field(default=None, ge=10, le=50000)
    condicoes_especificas: str | None = Field(default=None, max_length=2000)


class RenovarMedidaRequest(BaseModel):
    dias_adicionais: int = Field(ge=1, le=365)
    justificativa: str = Field(min_length=10, max_length=2000)


class RevogarMedidaRequest(BaseModel):
    motivo: str = Field(min_length=10, max_length=2000)


class MedidaProtetivaSchema(BaseModel):
    id: UUID
    numero_referencia: str
    ocorrencia_id: UUID
    delegado_id: UUID
    vitima_id: UUID
    agressor_id: UUID
    tipos_restricao: list[str]
    distancia_minima_metros: int | None
    data_inicio: str
    prazo_dias: int
    data_vencimento: str
    dias_restantes: int
    status: str
    condicoes_especificas: str | None
    motivo_revogacao: str | None
    justificativa_renovacao: str | None
    alerta_vencimento_enviado_em: str | None = None
    criada_em: str


class EnviarAlertaVencimentoRequest(BaseModel):
    email_destinatario: str | None = None


class ResultadoAlertaVencimentoSchema(BaseModel):
    sucesso: bool
    modo: str
    total_processadas: int
    alertas_enviados: int
    detalhes: list[dict]


class PaginaMedidasSchema(BaseModel):
    itens: list[MedidaProtetivaSchema]
    total: int
    offset: int
    limit: int


def _medida_schema(out: MedidaProtetivaOutput) -> MedidaProtetivaSchema:
    return MedidaProtetivaSchema(
        id=out.id,
        numero_referencia=out.numero_referencia,
        ocorrencia_id=out.ocorrencia_id,
        delegado_id=out.delegado_id,
        vitima_id=out.vitima_id,
        agressor_id=out.agressor_id,
        tipos_restricao=out.tipos_restricao,
        distancia_minima_metros=out.distancia_minima_metros,
        data_inicio=out.data_inicio,
        prazo_dias=out.prazo_dias,
        data_vencimento=out.data_vencimento,
        dias_restantes=out.dias_restantes,
        status=out.status,
        condicoes_especificas=out.condicoes_especificas,
        motivo_revogacao=out.motivo_revogacao,
        justificativa_renovacao=out.justificativa_renovacao,
        alerta_vencimento_enviado_em=out.alerta_vencimento_enviado_em,
        criada_em=out.criada_em,
    )


# ------------------------------------------------------------------ endpoints
@router.post("", response_model=MedidaProtetivaSchema, status_code=status.HTTP_201_CREATED)
async def conceder_medida(
    req: ConcederMedidaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    uc: InterfaceConcederMedida = Depends(get_conceder_medida),
) -> MedidaProtetivaSchema:
    """Formaliza a concessão de Medida Protetiva de Urgência (privativo do Delegado de Polícia)."""
    resultado = await uc.executar(
        ator,
        ConcederMedidaInput(
            ocorrencia_id=req.ocorrencia_id,
            vitima_id=req.vitima_id,
            agressor_id=req.agressor_id,
            tipos_restricao=req.tipos_restricao,
            prazo_dias=req.prazo_dias,
            data_inicio=req.data_inicio,
            distancia_minima_metros=req.distancia_minima_metros,
            condicoes_especificas=req.condicoes_especificas,
        ),
    )
    return _medida_schema(resultado)


@router.get("", response_model=PaginaMedidasSchema)
async def listar_medidas(
    status_filtro: list[str] | None = Query(None, alias="status"),
    ocorrencia_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceListarMedidas = Depends(get_listar_medidas),
) -> PaginaMedidasSchema:
    """Lista medidas protetivas com filtros e paginação."""
    itens, total = await uc.executar(
        ator,
        status=status_filtro,
        ocorrencia_id=ocorrencia_id,
        limit=limit,
        offset=offset,
    )
    return PaginaMedidasSchema(
        itens=[_medida_schema(i) for i in itens],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/{medida_id}/renovar", response_model=MedidaProtetivaSchema)
async def renovar_medida(
    medida_id: UUID,
    req: RenovarMedidaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    uc: InterfaceRenovarMedida = Depends(get_renovar_medida),
) -> MedidaProtetivaSchema:
    """Prorroga a vigência da medida protetiva com justificativa técnica registrada."""
    resultado = await uc.executar(
        ator,
        RenovarMedidaInput(
            medida_id=medida_id,
            dias_adicionais=req.dias_adicionais,
            justificativa=req.justificativa,
        ),
    )
    return _medida_schema(resultado)


@router.post("/{medida_id}/revogar", response_model=MedidaProtetivaSchema)
async def revogar_medida(
    medida_id: UUID,
    req: RevogarMedidaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    uc: InterfaceRevogarMedida = Depends(get_revogar_medida),
) -> MedidaProtetivaSchema:
    """Revoga formalmente a medida protetiva com fundamentação jurídica."""
    resultado = await uc.executar(
        ator,
        RevogarMedidaInput(
            medida_id=medida_id,
            motivo=req.motivo,
        ),
    )
    return _medida_schema(resultado)


@router.post("/verificar-vencimentos", response_model=ResultadoAlertaVencimentoSchema)
async def verificar_vencimentos(
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL)),
    uc: InterfaceEmitirAlertaVencimentoMedida = Depends(get_emitir_alerta_vencimento),
) -> ResultadoAlertaVencimentoSchema:
    """Verifica em lote medidas protetivas a expirar (< 72h) e dispara notificações e e-mails de alerta."""
    res = await uc.executar(ator=ator, medida_id=None)
    return ResultadoAlertaVencimentoSchema(**res)


@router.post("/{medida_id}/enviar-alerta-vencimento", response_model=ResultadoAlertaVencimentoSchema)
async def enviar_alerta_vencimento_individual(
    medida_id: UUID,
    req: EnviarAlertaVencimentoRequest | None = None,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL, Papel.AGENTE)),
    uc: InterfaceEmitirAlertaVencimentoMedida = Depends(get_emitir_alerta_vencimento),
) -> ResultadoAlertaVencimentoSchema:
    """Envia manual e formalmente alerta de vencimento de uma medida protetiva com notificação e e-mail."""
    email_dest = req.email_destinatario if req else None
    res = await uc.executar(ator=ator, medida_id=medida_id, email_destinatario_customizado=email_dest)
    return ResultadoAlertaVencimentoSchema(**res)
