"""
Adapter de entrada: /v1/inqueritos — Gestão de Inquéritos Policiais (RF06 / UC06 / sq06).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import ator_atual, exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    ConcluirInqueritoInput,
    ConexaoSugeridaOutput,
    InqueritoOutput,
    InstaurarInqueritoInput,
    InterfaceBuscarConexoesOcorrencia,
    InterfaceConcluirInquerito,
    InterfaceInstaurarInquerito,
    InterfaceListarInqueritos,
    InterfaceObterInquerito,
    InterfaceVincularOcorrenciasInquerito,
    OcorrenciaResumoInqueritoOutput,
    VincularOcorrenciasInput,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_buscar_conexoes_ocorrencia,
    get_concluir_inquerito,
    get_instaurar_inquerito,
    get_listar_inqueritos,
    get_obter_inquerito,
    get_vincular_ocorrencias_inquerito,
)

router = APIRouter(prefix="/v1/inqueritos", tags=["inqueritos"])

PAPEIS_CONSULTA = (Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL, Papel.AGENTE, Papel.ESCRIVAO)


# ------------------------------------------------------------------ schemas
class InstaurarInqueritoRequest(BaseModel):
    ementa: str = Field(min_length=10, max_length=5000)
    ocorrencias_iniciais_ids: list[UUID] = Field(default_factory=list)


class VincularOcorrenciasRequest(BaseModel):
    ocorrencias_ids: list[UUID] = Field(min_length=1)


class ConcluirInqueritoRequest(BaseModel):
    relatorio_final: str = Field(min_length=10, max_length=10000)


class OcorrenciaResumoInqueritoSchema(BaseModel):
    id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    data_hora_fato: str
    status: str


class InqueritoSchema(BaseModel):
    id: UUID
    numero: str
    ementa: str
    delegado_id: UUID
    status: str
    data_abertura: str
    atualizado_em: str
    ocorrencias: list[OcorrenciaResumoInqueritoSchema]
    relatorio_final: str | None = None
    motivo_arquivamento: str | None = None
    concluido_em: str | None = None


class PaginaInqueritosSchema(BaseModel):
    itens: list[InqueritoSchema]
    total: int
    offset: int
    limit: int


class ConexaoSugeridaSchema(BaseModel):
    ocorrencia_id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    score_similaridade: int
    motivos: list[str]


def _inquerito_schema(out: InqueritoOutput) -> InqueritoSchema:
    return InqueritoSchema(
        id=out.id,
        numero=out.numero,
        ementa=out.ementa,
        delegado_id=out.delegado_id,
        status=out.status,
        data_abertura=out.data_abertura,
        atualizado_em=out.atualizado_em,
        relatorio_final=out.relatorio_final,
        motivo_arquivamento=out.motivo_arquivamento,
        concluido_em=out.concluido_em,
        ocorrencias=[
            OcorrenciaResumoInqueritoSchema(
                id=o.id,
                numero_protocolo=o.numero_protocolo,
                natureza=o.natureza,
                localizacao=o.localizacao,
                data_hora_fato=o.data_hora_fato,
                status=o.status,
            )
            for o in out.ocorrencias
        ],
    )


# ------------------------------------------------------------------ endpoints
@router.post("", response_model=InqueritoSchema, status_code=status.HTTP_201_CREATED)
async def instaurar_inquerito(
    req: InstaurarInqueritoRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    uc: InterfaceInstaurarInquerito = Depends(get_instaurar_inquerito),
) -> InqueritoSchema:
    """Instaura um novo Inquérito Policial formal (privativo do Delegado de Polícia)."""
    resultado = await uc.executar(
        ator,
        InstaurarInqueritoInput(
            ementa=req.ementa,
            ocorrencias_iniciais_ids=req.ocorrencias_iniciais_ids,
        ),
    )
    return _inquerito_schema(resultado)


@router.get("", response_model=PaginaInqueritosSchema)
async def listar_inqueritos(
    status_filtro: list[str] | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceListarInqueritos = Depends(get_listar_inqueritos),
) -> PaginaInqueritosSchema:
    """Lista inquéritos com filtro de status e paginação."""
    itens, total = await uc.executar(ator, status=status_filtro, limit=limit, offset=offset)
    return PaginaInqueritosSchema(
        itens=[_inquerito_schema(i) for i in itens],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/conexoes/{ocorrencia_id}", response_model=list[ConexaoSugeridaSchema])
async def buscar_conexoes_ocorrencia(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceBuscarConexoesOcorrencia = Depends(get_buscar_conexoes_ocorrencia),
) -> list[ConexaoSugeridaSchema]:
    """Motor de sugestão de conexões criminais entre ocorrências (RF06 / sq06)."""
    sugestoes = await uc.executar(ator, ocorrencia_id)
    return [
        ConexaoSugeridaSchema(
            ocorrencia_id=s.ocorrencia_id,
            numero_protocolo=s.numero_protocolo,
            natureza=s.natureza,
            localizacao=s.localizacao,
            score_similaridade=s.score_similaridade,
            motivos=s.motivos,
        )
        for s in sugestoes
    ]


@router.get("/{inquerito_id}", response_model=InqueritoSchema)
async def obter_inquerito(
    inquerito_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceObterInquerito = Depends(get_obter_inquerito),
) -> InqueritoSchema:
    """Obtém detalhes do inquérito e suas ocorrências vinculadas."""
    resultado = await uc.executar(ator, inquerito_id)
    return _inquerito_schema(resultado)


@router.post("/{inquerito_id}/ocorrencias", response_model=InqueritoSchema)
async def vincular_ocorrencias(
    inquerito_id: UUID,
    req: VincularOcorrenciasRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    uc: InterfaceVincularOcorrenciasInquerito = Depends(get_vincular_ocorrencias_inquerito),
) -> InqueritoSchema:
    """Vincula uma ou mais ocorrências policiais validadas ao inquérito."""
    resultado = await uc.executar(
        ator,
        VincularOcorrenciasInput(
            inquerito_id=inquerito_id,
            ocorrencias_ids=req.ocorrencias_ids,
        ),
    )
    return _inquerito_schema(resultado)


@router.post("/{inquerito_id}/concluir", response_model=InqueritoSchema)
async def concluir_inquerito(
    inquerito_id: UUID,
    req: ConcluirInqueritoRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    uc: InterfaceConcluirInquerito = Depends(get_concluir_inquerito),
) -> InqueritoSchema:
    """Conclui o inquérito policial com relatório final circunstanciado."""
    resultado = await uc.executar(
        ator,
        ConcluirInqueritoInput(
            inquerito_id=inquerito_id,
            relatorio_final=req.relatorio_final,
        ),
    )
    return _inquerito_schema(resultado)
